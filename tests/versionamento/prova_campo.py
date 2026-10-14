"""Prova do modo local do SAP Operador, no QGIS 4 real e sem interface.

Roda o plugin de verdade (LocalProdToolsDockCtrl, o painel do modo local, os
algoritmos reais do DsgTools) com o pacote lido de um `public.sap_local`
FALSO (o Postgresql do plugin é trocado por um que devolve o pacote). Nenhum
sistema real é tocado e nenhuma rede é usada: os pedidos HTTP são registrados
e recusados.

Uso (Windows, QGIS 4.0.0):
    set QT_QPA_PLATFORM=offscreen
    set DSGTOOLS_PATH=<pasta que contém o pacote DsgTools>
    "<QGIS>\\bin\\python-qgis.bat" prova_campo.py <cenario> <saida.json> [<pasta que contém o pacote SAP_Operador>]

Cenários:
- `campo`: atividade do tipo 4 no modo local (contrato-sap.md, 9.4). O
  pacote é o que o SAP Gerente grava (sem `user`, `password` e senha do banco
  local; `versionamento` em `dados.atividade`, com `arquivo`, `sha256` e
  `enviado_sha256`), e o GeoPackage de campo é o de `campo_falso.py`. Monta o
  painel, carrega as camadas pelo botão do quadro Dados, confere SHA-256,
  `ogr`, tabelaDaCamada, estilos, apelidos, ações, domínios do modelo,
  regras de formatação, filtro de subfase, temas, menus, estatística de
  regras, grade de revisão, edição capturada pelos gatilhos, identidade
  nova, permissão da etapa, projeto reaberto e as recusas do arquivo.
- `local2`: atividade do tipo 2 no modo local (PostGIS fictício, processing
  gravado): o painel monta e as camadas carregam pelo botão.

Sem o terceiro argumento, o plugin é o deste repositório. Para reprovar o
estado anterior, extraia a revisão (`git archive <rev>`) numa pasta chamada
SAP_Operador e passe a pasta-mãe dela.
"""
import json
import os
import shutil
import sys
import tempfile
import traceback
import uuid
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

HERE=Path(__file__).resolve().parent
SCENARIO=sys.argv[1]
OUTPUT=Path(sys.argv[2])
PLUGIN_PARENT=Path(sys.argv[3]).resolve() if len(sys.argv)>3 else HERE.parents[2]

from qgis.core import QgsApplication  # noqa: E402

app=QgsApplication([],True)
app.initQgis()

log={'cenario':SCENARIO,'plugin':str(PLUGIN_PARENT.name),'checks':{},'processing':[],'mensagens':[],'rede':[]}
SENHA_LOCAL='senha-do-login-local'
DOMINIO={'format':'dsg-model/1','name':'edgv-teste','version':'1',
         'domains':[{'name':'tipo_massa_dagua','values':[{'code':1,'label':'Lago (1)'},{'code':2,'label':'Represa (2)'}]}],
         'classes':[{'name':'cobter_massa_dagua_a','identity':{'field':'dsg_id','kind':'uuid'},
                     'fields':[{'name':'tipo_massa_dagua','domain':'tipo_massa_dagua'},{'name':'nome','max_length':80}]}]}


def check(name,condition,detail=None):
    log['checks'][name]={'ok':bool(condition),'detalhe':detail}
    if not condition:
        raise AssertionError(name+(': '+str(detail) if detail is not None else ''))


def main():
    sys.path.insert(0,str(PLUGIN_PARENT))
    sys.path.insert(0,str(HERE))
    from qgis.testing import mocked
    import qgis.utils
    iface=mocked.get_iface()
    qgis.utils.iface=iface
    from qgis import processing as _qp  # noqa: F401
    from qgis.core import QgsProject,QgsVectorLayer,QgsDataSourceUri
    from qgis.PyQt import QtWidgets
    sys.path.insert(0,os.path.join(QgsApplication.prefixPath(),'python','plugins'))
    from processing.core.Processing import Processing
    Processing.initialize()
    dsgtools=os.environ.get('DSGTOOLS_PATH')
    if not dsgtools: raise SystemExit('Defina DSGTOOLS_PATH (pasta que contém o pacote DsgTools).')
    sys.path.insert(0,dsgtools)
    from DsgTools.core.DSGToolsProcessingAlgs.dsgtoolsProcessingAlgorithmProvider import DSGToolsProcessingAlgorithmProvider
    log['_provedor']=DSGToolsProcessingAlgorithmProvider()  # referência viva: o registro não a guarda
    QgsApplication.processingRegistry().addProvider(log['_provedor'])

    def note(kind):
        def show(parent,title,text,*args,**kwargs):
            log['mensagens'].append({'tipo':kind,'titulo':title,'texto':str(text)})
            return QtWidgets.QMessageBox.StandardButton.Ok
        return show
    for kind in ('critical','information','warning'):
        setattr(QtWidgets.QMessageBox,kind,staticmethod(note(kind)))
    QtWidgets.QMessageBox.question=staticmethod(lambda *a,**k:QtWidgets.QMessageBox.StandardButton.Yes)

    # Sem rede: todo pedido HTTP é registrado e recusado.
    import urllib.request
    import requests
    def offline(kind):
        def call(*args,**kwargs):
            log['rede'].append({'via':kind,'alvo':str(args[1] if kind=='requests' and len(args)>1 else args[0] if args else kwargs)[:200]})
            raise ConnectionError('sem rede na prova do modo local')
        return call
    urllib.request.urlopen=offline('urllib')
    requests.Session.request=offline('requests')

    import processing
    realRun=processing.run
    project=QgsProject.instance()

    def layerName(value):
        layer=project.mapLayer(value) if isinstance(value,str) else None
        return 'camada:'+layer.name() if layer is not None else value

    def normalize(value):
        if isinstance(value,dict): return {k:normalize(v) for k,v in value.items()}
        if isinstance(value,list): return [normalize(v) for v in value]
        if isinstance(value,str): return layerName(value)
        return value

    def fakePostgis(parameters):
        ids=[]
        for name in parameters['LAYER_LIST'].split(','):
            uri=QgsDataSourceUri(); uri.setConnection(parameters['HOST'],str(parameters['PORT']),parameters['DATABASE'],parameters['USER'],parameters['PASSWORD'])
            uri.setDataSource('edgv',name,'geom','','id')
            layer=QgsVectorLayer(uri.uri(False),name,'postgres'); project.addMapLayer(layer); ids.append(layer.id())
        return {'OUTPUT':ids}

    def recordingRun(algorithm,parameters,*args,**kwargs):
        algorithmId=algorithm if isinstance(algorithm,str) else algorithm.id()
        log['processing'].append({'alg':algorithmId,'params':normalize(parameters)})
        if algorithmId=='dsgtools:loadlayersfrompostgisalgorithm':
            return fakePostgis(parameters)
        if SCENARIO=='local2':
            if algorithmId=='dsgtools:grouplayers':
                root=project.layerTreeRoot()
                for source in parameters['INPUT_LAYERS']:
                    name=QgsDataSourceUri(source).database()
                    if name and root.findGroup(name) is None: root.addGroup(name)
            if algorithmId=='dsgtools:createreviewgridalgorithm':
                return {'OUTPUT':None}
            return {'OUTPUT':[]}
        return realRun(algorithm,parameters,*args,**kwargs)
    processing.run=recordingRun

    import servidor_falso
    # O pacote como o SAP o devolve (envelope com dados), o mesmo que o SAP Gerente lê.
    pacote={'version':'3.33.0','success':True,'message':'ok','dados':servidor_falso.Estado('versionado' if SCENARIO=='campo' else 'tipo2').pacote()}
    pasta=Path(tempfile.mkdtemp(prefix='sap_campo_'))
    try:
        if SCENARIO=='campo':
            campo(pacote,pasta,project,iface)
        else:
            local2(pacote,project,iface)
    finally:
        shutil.rmtree(pasta,ignore_errors=True)


class Recorder:
    def __init__(self,name): self.name=name
    def __getattr__(self,attribute):
        def call(*args,**kwargs):
            log.setdefault('stubs',[]).append(self.name+'.'+attribute)
            return Recorder(self.name+'.'+attribute)
        return call


class Fme:
    def getSapRoutines(self,config): return []


class Database:
    def createPostgres(self,*args):
        log['banco']=[str(a) for a in args]
        return self
    def getAttributeValueMap(self,name,schema): return {}


class Tools:
    def getTool(self,name,controller):
        log.setdefault('ferramentas',[]).append(name)
        return Recorder(name)


def montar(pacote,iface):
    """Controlador do modo local com o `public.sap_local` falso; devolve (ctrl, painel)."""
    from SAP_Operador.modules.qgis.qgisApi import QgisApi
    from SAP_Operador.modules.sap.controllers.localSapCtrl import LocalSapCtrl
    from SAP_Operador.controllers import localProdToolsDockCtrl as module
    from SAP_Operador.modules.dsgTools.factories.processingQgisFactory import ProcessingQgisFactory

    class SapLocal:
        def __init__(self,dbName,dbUser,dbHost,dbPort,dbPass):
            log.setdefault('banco_local',[]).append([dbName,dbUser,dbHost,str(dbPort),'***' if dbPass else ''])
        def execute(self,query,params):
            if 'json_atividade' in query: return [[json.dumps(pacote)]]
            if 'EXTRACT' in query: return [(None,None,None,None)]
            if 'count(*)' in query: return [[1]]
            return []
    module.Postgresql=SapLocal

    qgisApi=QgisApi(); qgisApi.load=lambda:None
    qgisApi.loadLayerActions=lambda layerIds:None
    # Como o main.initGui do plugin: provedor e ligação das camadas que entram no projeto.
    from SAP_Operador.modules import versionamento
    versionamento.registrar(iface)
    ctrl=module.LocalProdToolsDockCtrl(sap=LocalSapCtrl(qgisApi),qgis=qgisApi,databaseFactory=Database(),
                                       processingFactoryDsgTools=ProcessingQgisFactory(),fme=Fme(),
                                       prodToolsSettings=Recorder('settings'),toolFactoryDsgTools=Tools())
    check('login local (banco do sap_local)',ctrl.authUser('operador','senha','localhost','5432','sap_local'))
    try:
        dock=ctrl.loadDockWidget('operador',SENHA_LOCAL,'localhost','5432','sap_local')
        built=dock is not None
        error=None
    except Exception as e:
        built=False; error=''.join(traceback.format_exception(type(e),e,e.__traceback__))[-1500:]
        dock=None
    check('painel do modo local montado',built,error)
    return ctrl,dock


def carregarPeloBotao(dock):
    """Clica em "Carregar camadas" do quadro Dados do painel do modo local."""
    from SAP_Operador.widgets.activityData import ActivityData
    widgets=dock.findChildren(ActivityData)
    check('quadro Dados no painel do modo local',len(widgets)==1,len(widgets))
    widgets[0].on_loadLayersBtn_clicked()


def pacoteDoGerente(pacote,versionamento):
    """O pacote como o SAP Gerente grava em public.sap_local (contrato.pacoteParaSAPLocal)."""
    pacote=json.loads(json.dumps(pacote))
    pacote['dados'].pop('versionamento',None)
    pacote['dados'].pop('login_info',None)
    pacote['dados']['atividade']['versionamento']=versionamento
    pacote['dados']['atividade'].pop('fme',None); pacote['dados']['atividade'].pop('insumos',None)
    pacote['local_db']={'alias':'local','database':'sap_local','host':'localhost','port':'5432','username':'operador'}
    return pacote


def campo(pacoteRemoto,pasta,project,iface):
    import campo_falso
    from qgis.core import QgsSettings
    from qgis.PyQt import QtWidgets
    repo=str(uuid.uuid4()); pai=str(uuid.uuid4())
    ids={k:str(uuid.uuid4()) for k in ('a','b','c','p1','p2')}
    square=lambda x:'POLYGON(({0} -30,{1} -30,{1} -29.99,{0} -29.99,{0} -30))'.format(x,x+0.01)
    classes=[
        {'name':'cobter_massa_dagua_a','geometry':'POLYGON','fields':[('nome','TEXT'),('tipo_massa_dagua','INTEGER'),('subfase_id','INTEGER')],
         'rows':[{'dsg_id':ids['a'],'wkt':square(-51.0),'nome':'Lago A','tipo_massa_dagua':1,'subfase_id':7},
                 {'dsg_id':ids['b'],'wkt':square(-50.98),'nome':'Lago B','tipo_massa_dagua':None,'subfase_id':7},
                 {'dsg_id':ids['c'],'wkt':square(-50.96),'nome':'Lago C','tipo_massa_dagua':2,'subfase_id':7}]},
        {'name':'aux_revisao_p','geometry':'POINT','fields':[('descricao','TEXT'),('subfase_id','INTEGER'),('situacao_correcao','INTEGER'),('justificativa','TEXT')],
         'rows':[{'dsg_id':ids['p1'],'wkt':'POINT(-50.99 -29.995)','descricao':'da subfase','subfase_id':7},
                 {'dsg_id':ids['p2'],'wkt':'POINT(-50.97 -29.995)','descricao':'de outra subfase','subfase_id':8}]},
        {'name':'aux_grid_revisao_a','geometry':'POLYGON','fields':[('unidade_trabalho_id','INTEGER'),('etapa_id','INTEGER'),('rank','INTEGER'),('visited','INTEGER')],'rows':[]},
    ]
    permissions={'cobter_massa_dagua_a':{'insert':True,'delete':True,'geometry':True,'fields':None},
                 'aux_revisao_p':{'insert':False,'delete':False,'geometry':False,'fields':['situacao_correcao','justificativa']},
                 'aux_grid_revisao_a':{'insert':True,'delete':True,'geometry':True,'fields':None}}
    origem=pasta/'gerente'; origem.mkdir()
    arquivo=repo+'.gpkg'
    gpkg=campo_falso.criar(origem/arquivo,repo,pai,classes,permissions,modelo=DOMINIO)
    import hashlib
    sha=hashlib.sha256(Path(gpkg).read_bytes()).hexdigest()
    datasets=[{'schema':'edgv','nome':c['name'],'dataset':c['name']} for c in classes]
    versionamento={'repo_id':repo,'servico':servidor_path(),'papel':'atividade','datasets':datasets,
                   'arquivo':arquivo,'sha256':sha,'enviado_sha256':'0'*64}
    pacote=pacoteDoGerente(pacoteRemoto,versionamento)
    pacote['dados']['atividade']['monitoramento']=[]
    pacote['dados']['atividade']['menus']=[{'nome':'Hidrografia','definicao_menu':json.dumps(
        {'menus':[{'menuName':'Hidrografia','tabs':[{'tabName':'Massas','buttons':[
            {'buttonName':'Lago','buttonLayer':'cobter_massa_dagua_a','buttonAttributes':{'tipo_massa_dagua':'Lago (1)'},
             'buttonSuppressForm':False,'buttonAcquisitionTool':''}]}]}]})}]
    campoDir=pasta/'campo'; campoDir.mkdir()
    shutil.copy2(gpkg,campoDir/arquivo)
    trabalho=campoDir/arquivo
    settings=QgsSettings(); key='productiontools:campo:'+repo
    settings.remove(key)
    escolhas=[]
    def escolher(parent,title,directory='',filter_='',*args,**kwargs):
        escolhas.append({'titulo':title,'filtro':filter_})
        return str(trabalho),''
    QtWidgets.QFileDialog.getOpenFileName=staticmethod(escolher)
    try:
        campoProva(pacote,versionamento,trabalho,pasta,project,iface,escolhas,repo,campo_falso,ids,classes,permissions,key)
    finally:
        QgsSettings().remove(key)


def servidor_path():
    return '/api/versionamento/servico'


def campoProva(pacote,versionamento,trabalho,pasta,project,iface,escolhas,repo,campo_falso,ids,classes,permissions,key):
    from qgis.core import QgsFeature,QgsGeometry,QgsVectorLayer,QgsVectorLayerUtils
    from SAP_Operador.modules.versionamento import camadas
    ctrl,dock=montar(pacote,iface)
    check('pacote sem segredo: o banco local vem do login do operador',
          ctrl.sapActivity.getDatabasePassword()==SENHA_LOCAL and 'password' not in pacote and 'user' not in pacote)
    check('versionamento lido em dados.atividade, com arquivo e sha256',
          ctrl.sapActivity.getVersioning() is not None and ctrl.sapActivity.getVersioning().get('arquivo')==versionamento['arquivo'])
    carregarPeloBotao(dock)
    layers={l.name():l for l in project.mapLayers().values() if isinstance(l,QgsVectorLayer) and l.name()!='moldura'}
    log['camadas']={n:{'provedor':l.providerType(),'valida':l.isValid(),'fonte':l.source().split('|')[-1]} for n,l in layers.items()}
    check('nenhum pedido de rede no carregamento',not log['rede'],log['rede'])
    check('GeoPackage de campo pedido ao operador uma vez, pelo nome do pacote',
          len(escolhas)==1 and versionamento['arquivo'] in escolhas[0]['filtro'],escolhas)
    check('SHA-256 do pacote conferido e marcado ao lado do arquivo',
          getattr(ctrl,'fieldGaps',{}).get('estado')=='conferido' and os.path.isfile(str(trabalho)+'.sap-conferido.json'),getattr(ctrl,'fieldGaps',None))
    cobter=layers.get('cobter_massa_dagua_a'); revisao=layers.get('aux_revisao_p')
    tabela=campo_falso.tabela('cobter_massa_dagua_a')
    check('camadas abertas pelo ogr, do GeoPackage de campo',
          cobter is not None and revisao is not None and cobter.providerType()=='ogr' and cobter.isValid() and
          cobter.source().replace('\\','/').startswith(str(trabalho).replace('\\','/')) and cobter.source().endswith('layername='+tabela),
          log['camadas'])
    check('tabelaDaCamada da camada de campo pelo datasets do pacote',
          camadas.tabelaDaCamada(cobter)==('edgv','cobter_massa_dagua_a') and camadas.tabelaDaCamada(revisao)==('edgv','aux_revisao_p')
          and cobter.dataProvider().uri().table()=='',(camadas.tabelaDaCamada(cobter),camadas.tabelaDaCamada(revisao)))
    check('feições lidas do arquivo',len(list(cobter.getFeatures()))==3)
    algs=[p['alg'] for p in log['processing']]
    check('sem banco e sem os algoritmos que casam por uri().table()',
          not log.get('banco') and not any(a in algs for a in ('dsgtools:loadlayersfrompostgisalgorithm','dsgtools:assignaliasestolayersalgorithm',
                                                                 'dsgtools:assignactionstolayersalgorithm','dsgtools:assignformatrulestolayersalgorithm',
                                                                 'dsgtools:loadthemes','dsgtools:assignvaluemaptolayersalgorithm')),algs)
    check('estilo do pacote',cobter.styleManager().currentStyle()=='padrao',cobter.styleManager().styles())
    alias=cobter.attributeAlias(cobter.fields().indexFromName('nome'))
    check('apelido do pacote',alias=='Nome da massa d água',alias)
    actions=[a.name() for a in cobter.actions().actions()]
    check('ação do pacote','Doc MGCP' in actions,actions)
    tipo=cobter.fields().indexFromName('tipo_massa_dagua')
    setup=cobter.editorWidgetSetup(tipo)
    check('domínio do modelo do clone no formulário (ValueMap)',setup.type()=='ValueMap' and 'Lago (1)' in json.dumps(setup.config(),ensure_ascii=False),
          [setup.type(),setup.config()])
    styles=cobter.conditionalStyles().fieldStyles('tipo_massa_dagua')
    errors=sorted(f['attribute_error_description'] for f in cobter.getFeatures())
    check('regras de formatação na camada de campo',len(styles)==1 and errors==['','','Tipo de massa d água vazio'],[[s.rule() for s in styles],errors])
    subfase='"subfase_id" = \'7\''
    check('filtro de subfase na camada de apontamento',revisao.subsetString()==subfase and [f['descricao'] for f in revisao.getFeatures()]==['da subfase'],
          (revisao.subsetString(),[f['descricao'] for f in revisao.getFeatures()]))
    themes=project.mapThemeCollection().mapThemes()
    check('tema do pacote','Hidrografia' in themes and cobter.id() in project.mapThemeCollection().mapThemeVisibleLayerIds('Hidrografia'),themes)
    menus=ctrl.getSapMenus()
    button=menus[0]['menus'][0]['tabs'][0]['buttons'][0]
    from DsgTools.Modules.qgis.controllers.qgisCtrl import QgisCtrl
    found=QgisCtrl().getVectorLayersByName(button['buttonLayer'])
    check('menu de aquisição do DsgTools acha a camada de campo',[l.id() for l in found]==[cobter.id()] and
          ctrl.sapActivity.getMenus()[0]['menus'][0]['tabs'][0]['buttons'][0]['buttonLayer']=='cobter_massa_dagua_a',
          (button['buttonLayer'],[l.name() for l in found]))
    shown=[]
    class Dialog:
        def show(self,*args): shown.append(args[2])
    messages=ctrl.messageFactory
    ctrl.messageFactory=type('F',(),{'createMessage':lambda self,name:Dialog()})()
    statistics=ctrl.runRuleStatistics(ctrl.sapActivity.getRuleRoutines()[0])
    ctrl.messageFactory=messages
    check('estatística de regras acha a camada de campo',statistics=={'[RULES] : Preencher atributo':['cobter_massa_dagua_a']} and shown==[statistics],statistics)
    grid=next((l for l in project.mapLayers().values() if camadas.tabelaDaCamada(l)==('edgv','aux_grid_revisao_a')),None)
    check('grade de revisão do arquivo, filtrada por unidade de trabalho e etapa',
          grid is not None and grid.providerType()=='ogr' and grid.subsetString()=='unidade_trabalho_id = 55 AND etapa_id = 9' and
          'dsgtools:createreviewgridalgorithm' in algs and 'ReviewToolBar' in log.get('ferramentas',[]),
          (grid.subsetString() if grid else None,grid.providerType() if grid else None,'dsgtools:createreviewgridalgorithm' in algs,log.get('ferramentas')))
    log['estatistica']=statistics

    # Edição direta: gatilhos de captura e identidade nova ------------------------------
    pending=campo_falso.pendentes(trabalho)
    index=cobter.fields().indexOf('dsg_id')
    check('dsg_id só leitura e com identidade nova no formulário',
          cobter.editFormConfig().readOnly(index) and 'uuid' in cobter.defaultValueDefinition(index).expression())
    check('editar',cobter.startEditing())
    novo=QgsVectorLayerUtils.createFeature(cobter,QgsGeometry.fromWkt('POLYGON((-50.94 -30,-50.93 -30,-50.93 -29.99,-50.94 -29.99,-50.94 -30))'),
                                           {cobter.fields().indexOf('nome'):'Lago novo',tipo:1})
    novoId=novo['dsg_id']
    copia=QgsFeature(novo); copia.setAttribute(index,ids['a']); copia.setAttribute(cobter.fields().indexOf('nome'),'Lago colado')
    copia.setGeometry(QgsGeometry.fromWkt('POLYGON((-50.92 -30,-50.91 -30,-50.91 -29.99,-50.92 -29.99,-50.92 -30))'))
    menu=QgsFeature(novo); menu.setAttribute(index,"'lower(substr(uuid(),2,36))'"); menu.setAttribute(cobter.fields().indexOf('nome'),'Lago do menu')
    menu.setGeometry(QgsGeometry.fromWkt('POLYGON((-50.90 -30,-50.89 -30,-50.89 -29.99,-50.90 -29.99,-50.90 -30))'))
    check('adicionar',cobter.addFeature(novo) and cobter.addFeature(copia) and cobter.addFeature(menu))
    b=next(f for f in cobter.getFeatures() if f['dsg_id']==ids['b'])
    cobter.changeAttributeValue(b.id(),cobter.fields().indexOf('nome'),'Lago B renomeado')
    check('salvar no arquivo',cobter.commitChanges(),cobter.commitErrors())
    novas={f['nome']:f['dsg_id'] for f in cobter.getFeatures() if f['nome'] in ('Lago novo','Lago colado','Lago do menu')}
    from SAP_Operador.modules.versionamento import model as model_rules
    check('feição nova com a identidade do formulário',novas.get('Lago novo')==novoId and model_rules.is_canonical_uuid(novoId),novas)
    check('identidade copiada ou inválida trocada antes de gravar',
          len(set(novas.values()))==3 and all(model_rules.is_canonical_uuid(v) for v in novas.values()) and ids['a'] not in novas.values(),novas)
    versions=campo_falso.versoes(trabalho,'cobter_massa_dagua_a')
    check('edição capturada pelos gatilhos do GeoPackage',campo_falso.pendentes(trabalho)==pending+4 and
          sorted(v[1] for v in versions if v[0]==1 and v[2]=='external:unattributed')==sorted(novas.values()) and
          any(v[0]==2 and v[1]==ids['b'] for v in versions),versions[-5:])

    # Permissão da etapa ----------------------------------------------------------------
    from qgis.core import QgsApplication
    rIndex=revisao.fields().indexOf('descricao'); jIndex=revisao.fields().indexOf('justificativa')
    check('campo fora da permissão só leitura no formulário',revisao.editFormConfig().readOnly(rIndex) and not revisao.editFormConfig().readOnly(jIndex))
    revisao.startEditing()
    ponto=QgsVectorLayerUtils.createFeature(revisao,QgsGeometry.fromWkt('POINT(-50.98 -29.995)'),{revisao.fields().indexOf('subfase_id'):7})
    revisao.addFeature(ponto)
    QgsApplication.processEvents()
    p1=next(f for f in revisao.getFeatures() if f['dsg_id']==ids['p1'])
    revisao.changeAttributeValue(p1.id(),rIndex,'mudou')
    QgsApplication.processEvents()
    revisao.changeAttributeValue(p1.id(),jIndex,'apontamento conferido')
    QgsApplication.processEvents()
    buffer=revisao.editBuffer()
    check('inserção e campo fora da permissão desfeitos na hora',
          not buffer.addedFeatures() and list(buffer.changedAttributeValues().get(p1.id(),{}).keys())==[jIndex],
          (len(buffer.addedFeatures()),dict(buffer.changedAttributeValues())))
    avisos=mensagensDaGuarda(revisao)
    check('aviso da permissão para cada edição desfeita',
          any('inserir feição' in t for t in avisos) and any('alterar o campo descricao' in t for t in avisos),avisos)
    check('salvar o que a etapa permite',revisao.commitChanges(),revisao.commitErrors())
    stored={f['dsg_id']:(f['descricao'],f['justificativa']) for f in revisao.getFeatures()}
    check('relido no arquivo',stored.get(ids['p1'])==('da subfase','apontamento conferido'),stored)

    # Grade nova gravada no arquivo, como o ReviewToolBar do plugin a grava -----------
    output=QgsVectorLayer('Polygon?crs=EPSG:4674&field=unidade_trabalho_id:integer&field=etapa_id:integer&field=rank:integer&field=visited:integer','saida','memory')
    cells=[]
    for x,rank in ((-51.0,1),(-50.99,2)):
        f=QgsFeature(output.fields()); f.setAttributes([55,9,rank,0])
        f.setGeometry(QgsGeometry.fromWkt('POLYGON(({0} -30,{1} -30,{1} -29.99,{0} -29.99,{0} -30))'.format(x,x+0.01))); cells.append(f)
    output.dataProvider().addFeatures(cells)
    from SAP_Operador.modules.dsgTools.toolbarLaunchers.reviewToolbar import ReviewToolBar
    ReviewToolBar(ctrl).populateGridLayerWithOutputLayerFeatures(grid,output)
    gridIds=[f['dsg_id'] for f in grid.getFeatures()]
    check('grade de revisão gravada no arquivo com identidade',len(gridIds)==2 and all(model_rules.is_canonical_uuid(i) for i in gridIds)
          and not grid.isModified(),gridIds)

    # Projeto reaberto: a camada volta reconhecida e com a permissão ---------------------
    projectFile=str(pasta/'projeto.qgz')
    check('projeto salvo',project.write(projectFile))
    project.clear()
    check('projeto reaberto',project.read(projectFile))
    again={camadas.tabelaDaCamada(l):l for l in project.mapLayers().values() if camadas.ehDeCampo(l)}
    reaberta=again.get(('edgv','aux_revisao_p'))
    check('camada de campo reconhecida no projeto reaberto',reaberta is not None and reaberta.isValid() and
          reaberta.subsetString()==subfase,list(again))
    reaberta.startEditing()
    reaberta.addFeature(QgsVectorLayerUtils.createFeature(reaberta,QgsGeometry.fromWkt('POINT(-50.98 -29.995)'),{}))
    QgsApplication.processEvents()
    check('permissão religada no projeto reaberto',not reaberta.editBuffer().addedFeatures())
    reaberta.rollBack()

    # Segunda carga: o arquivo já foi aberto e editado (bytes mudaram) ----------------
    project.clear()
    ctrl.loadActivityLayersByNames(['cobter_massa_dagua_a'])
    check('segunda carga: pasta lembrada, arquivo em edição aceito pela identidade',
          len(escolhas)==1 and ctrl.fieldGaps.get('estado')=='em edição' and
          any(camadas.tabelaDaCamada(l)==('edgv','cobter_massa_dagua_a') for l in project.mapLayers().values()),
          (len(escolhas),getattr(ctrl,'fieldGaps',None)))

    # Recusas do arquivo ----------------------------------------------------------------
    from SAP_Operador.modules.versionamento import campo as campoMod
    outra=pasta/'outra'; outra.mkdir()
    campo_falso.criar(outra/versionamento['arquivo'],repo,'pai',classes,permissions)
    from qgis.core import QgsSettings
    QgsSettings().setValue(key,str(outra))
    project.clear(); before=len(log['mensagens'])
    ctrl.loadActivityLayersByNames(['cobter_massa_dagua_a'])
    texts=[m['texto'] for m in log['mensagens'][before:]]
    check('arquivo que não confere com o SHA-256 recusado, nada carregado',
          any('não confere com o pacote local' in t for t in texts) and not project.mapLayers(),texts)
    def refused(path,meta=None,repoId=repo):
        import hashlib
        campo_falso.criar(path,repoId,'pai',classes,permissions,meta_extra=meta)
        package=dict(versionamento,sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())
        try:
            campoMod.conferirArquivo(str(path),package); return None
        except campoMod.CampoError as error:
            return str(error)
    other=refused(pasta/'repo.gpkg',repoId=str(uuid.uuid4()))
    check('arquivo de outro repositório recusado',other and 'é do repositório' in other,other)
    closed=refused(pasta/'fechado.gpkg',meta={'closure':'{"kind":"merged"}'})
    check('clone encerrado recusado',closed and 'encerrado' in closed,closed)
    for wrong in ({'arquivo':'../x.gpkg'},{'sha256':''}):
        try:
            campoMod.nomeDoArquivo(dict(versionamento,**wrong)); campoMod.conferirArquivo(str(trabalho),dict(versionamento,**wrong)); ok=False
        except campoMod.CampoError:
            ok=True
        check('pacote sem nome simples ou sem SHA-256 recusado: '+json.dumps(wrong),ok)
    check('nenhum pedido de rede em toda a prova',not log['rede'],log['rede'])


def mensagensDaGuarda(layer):
    from SAP_Operador.modules.versionamento.campo import GuardaDeCampo
    out=[]
    for child in layer.findChildren(GuardaDeCampo):
        out+=child.mensagens
    return out


def local2(pacoteRemoto,project,iface):
    pacote=json.loads(json.dumps(pacoteRemoto))
    pacote['dados'].pop('login_info',None)
    pacote['local_db']={'alias':'local','database':'producao_local','host':'localhost','port':'5432','username':'operador'}
    pacote['dados']['atividade']['monitoramento']=[]
    ctrl,dock=montar(pacote,iface)
    carregarPeloBotao(dock)
    algs=[p['alg'] for p in log['processing']]
    check('camadas pelo PostGIS do banco local',algs and algs[0]=='dsgtools:loadlayersfrompostgisalgorithm' and
          log['processing'][0]['params']['PASSWORD']==SENHA_LOCAL,algs)
    themes=[p['params'] for p in log['processing'] if p['alg']=='dsgtools:loadthemes']
    check('temas como lista de temas (definicao_tema lida)',themes and json.loads(themes[0]['TEXT'])[0]['nome']=='Hidrografia',themes)
    aliases=[p['params'] for p in log['processing'] if p['alg']=='dsgtools:assignaliasestolayersalgorithm']
    check('apelidos como o texto da definição',aliases and json.loads(aliases[0]['TEXT'])[0]['camadaNome']=='cobter_massa_dagua_a',aliases)
    check('grade de revisão pedida ao banco local',
          sum(1 for p in log['processing'] if p['alg']=='dsgtools:loadlayersfrompostgisalgorithm')==2,algs)
    check('nenhum pedido de rede',not log['rede'],log['rede'])


if __name__=='__main__':
    status=0
    try:
        main()
    except BaseException as error:
        status=1
        log['erro']=''.join(traceback.format_exception(type(error),error,error.__traceback__))[-4000:]
    finally:
        def shown(value):
            try: return str(value)
            except RuntimeError: return '<objeto do QGIS já destruído>'
        log.pop('_provedor',None)
        OUTPUT.write_text(json.dumps(log,ensure_ascii=False,indent=2,default=shown),encoding='utf-8')
        print(json.dumps({'cenario':SCENARIO,'status':'ok' if status==0 else 'falhou','checks':sum(1 for c in log['checks'].values() if c['ok']),
                          'erro':(log.get('erro') or '').strip().splitlines()[-1:] },ensure_ascii=False),flush=True)
        os._exit(status)

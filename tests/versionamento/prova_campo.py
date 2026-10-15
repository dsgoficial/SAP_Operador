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
  regras, grade de revisão, valores padrão do modelo do clone no formulário,
  edição capturada pelos gatilhos, identidade nova, permissão da etapa, a
  trava de apontamentos não resolvidos na correção, projeto reaberto e as
  recusas do arquivo. O painel se refaz (`reload`) como painel do modo
  local, o usuário da atividade é o `usuario_uuid` do SAP 3.0, o tipo de
  produto é o `subtipo_produto` e o modelo da atividade local não tem método
  repetido (morto).
- `recusa`: o `public.sap_local` gravado por um SAP Gerente antigo traz
  atividade do tipo 2, 3 ou do tipo 4 sem a seção `versionamento`. O login
  do modo local a recusa com o motivo, sem exceção, sem painel e sem
  camada; o pacote sem o tipo e com a base versionada é aceito.

Sem o terceiro argumento, o plugin é o deste repositório. Para reprovar o
estado anterior, extraia a revisão (`git archive <rev>`) numa pasta chamada
SAP_Operador e passe a pasta-mãe dela.
"""
import inspect
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
                     # Valor padrão literal (entra no formulário) e por expressão
                     # (ignorado, como no provedor remoto), na forma do dsg-model/1.
                     'fields':[{'name':'tipo_massa_dagua','domain':'tipo_massa_dagua'},
                               {'name':'nome','max_length':80,'default':{'expression':"'sem nome'"}},
                               {'name':'subfase_id','default':{'value':7}}]}]}


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

    def recordingRun(algorithm,parameters,*args,**kwargs):
        algorithmId=algorithm if isinstance(algorithm,str) else algorithm.id()
        log['processing'].append({'alg':algorithmId,'params':normalize(parameters)})
        if SCENARIO=='recusa':
            # Nada deve chegar aqui; o algoritmo não roda.
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
            recusa(pacote,project,iface)
    finally:
        shutil.rmtree(pasta,ignore_errors=True)


class Recorder:
    def __init__(self,name): self.name=name
    def __getattr__(self,attribute):
        def call(*args,**kwargs):
            log.setdefault('stubs',[]).append(self.name+'.'+attribute)
            return Recorder(self.name+'.'+attribute)
        return call


class Database:
    def createPostgres(self,*args):
        log['banco']=[str(a) for a in args]
        return self
    def getAttributeValueMap(self,name,schema): return {}


class Tools:
    def getTool(self,name,controller):
        log.setdefault('ferramentas',[]).append(name)
        return Recorder(name)


def controlador(pacote,iface):
    """Controlador do modo local com o `public.sap_local` falso, antes do login."""
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
    kwargs=dict(sap=LocalSapCtrl(qgisApi),qgis=qgisApi,processingFactoryDsgTools=ProcessingQgisFactory(),
                prodToolsSettings=Recorder('settings'),toolFactoryDsgTools=Tools())
    parameters=inspect.signature(module.LocalProdToolsDockCtrl.__init__).parameters
    if 'databaseFactory' in parameters:
        kwargs['databaseFactory']=Database()  # plugin anterior à 4.4.0, para reprovar o estado anterior
    if 'fme' in parameters:
        # Plugin anterior à 4.3.0: o gerenciador sem rotina, como era aqui.
        kwargs['fme']=type('GerenciadorAntigo',(),{'getSapRoutines':lambda self,config:[]})()
    return module.LocalProdToolsDockCtrl(**kwargs)


def montar(pacote,iface):
    """Controlador do modo local com o `public.sap_local` falso; devolve (ctrl, painel)."""
    ctrl=controlador(pacote,iface)
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

    # Valores padrão do modelo do clone no formulário ------------------------------
    subfaseIndex=cobter.fields().indexOf('subfase_id'); nomeIndex=cobter.fields().indexOf('nome')
    padrao=QgsVectorLayerUtils.createFeature(cobter,QgsGeometry.fromWkt('POLYGON((-50.94 -30,-50.93 -30,-50.93 -29.99,-50.94 -29.99,-50.94 -30))'))
    check('valor padrão literal do modelo do clone no formulário (o padrão por expressão fica de fora, como no remoto)',
          cobter.defaultValueDefinition(subfaseIndex).expression()=='7' and padrao['subfase_id']==7 and
          not cobter.defaultValueDefinition(nomeIndex).expression() and padrao['nome'] in (None,'') and
          'uuid' in cobter.defaultValueDefinition(cobter.fields().indexOf('dsg_id')).expression(),
          (cobter.defaultValueDefinition(subfaseIndex).expression(),cobter.defaultValueDefinition(nomeIndex).expression(),
           padrao['subfase_id'],padrao['nome']))
    from SAP_Operador.modules.versionamento import campo as campoPadrao
    from SAP_Operador.modules.versionamento import model as modelPadrao
    esperado={'quando':("date","'2026-10-14'"),'ativo':('boolean','TRUE'),'peso':('real','1.5'),'rotulo':('text',"'d''água'")}
    regras=modelPadrao.class_rules(campoPadrao._modeloDaApi(json.dumps({'format':'dsg-model/1','name':'m','version':'1','domains':[],
        'classes':[{'name':'c','fields':[{'name':'quando','default':{'value':'2026-10-14'}},{'name':'ativo','default':{'value':True}},
                                         {'name':'peso','default':{'value':1.5}},{'name':'rotulo','default':{'value':"d'água"}}]}]})),
        {'c':[]},{'name':'c','fields':[{'name':nome,'kind':tipo} for nome,(tipo,_) in esperado.items()]})
    obtido={nome:campoPadrao.padraoDoModelo({'name':nome,'kind':tipo},regras) for nome,(tipo,_) in esperado.items()}
    check('valor padrão de cada tipo do modelo vira expressão literal do QGIS',
          obtido=={nome:expressao for nome,(_,expressao) in esperado.items()},obtido)

    # Edição direta: gatilhos de captura e identidade nova ------------------------------
    pending=campo_falso.pendentes(trabalho)
    index=cobter.fields().indexOf('dsg_id')
    check('dsg_id só leitura e com identidade nova no formulário',
          cobter.editFormConfig().readOnly(index) and 'uuid' in cobter.defaultValueDefinition(index).expression())
    check('editar',cobter.startEditing())
    novo=QgsVectorLayerUtils.createFeature(cobter,QgsGeometry.fromWkt('POLYGON((-50.94 -30,-50.93 -30,-50.93 -29.99,-50.94 -29.99,-50.94 -30))'),
                                           {cobter.fields().indexOf('nome'):'Lago novo',tipo:1})
    novoId=novo['dsg_id']
    check('feição nova do formulário com o padrão do modelo',novo['subfase_id']==7,novo['subfase_id'])
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

    # Trava de apontamentos não resolvidos na correção (antes da edição) ------------
    trava=travaDeApontamentos(ctrl)
    check('correção com apontamento não resolvido: a finalização é barrada',
          trava['avisos']==['Existem apontamentos não resolvidos!'] and not trava['dialogo'],trava)

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
    trava=travaDeApontamentos(ctrl)
    check('correção com o apontamento justificado: a finalização segue para o diálogo',
          not trava['avisos'] and len(trava['dialogo'])==1,trava)

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
    defeitosDoModoLocal(ctrl,dock,pacote)
    check('nenhum pedido de rede em toda a prova',not log['rede'],log['rede'])


def travaDeApontamentos(ctrl):
    """Finalizar na etapa de correção (tipo_etapa_id 3): o qgisApi devolve
    False quando há apontamento sem resolução, e é aí que a finalização para,
    como no remoto. Até a 4.3.0 o modo local testava `checkStep` sem o `not`:
    barrava o apontamento resolvido e deixava passar o não resolvido."""
    atividade=ctrl.sapActivity.getData()['dados']['atividade']
    original=atividade['tipo_etapa_id']
    atividade['tipo_etapa_id']=3
    dialogo=[]
    # O LocalSapCtrl não tem o diálogo de finalização (o botão fica escondido no
    # painel do modo local): a chamada é registrada.
    ctrl.sap.showEndActivityDialog=lambda *args:dialogo.append(args) or False
    before=len(log['mensagens'])
    try:
        ctrl.showEndActivityDialog(); erro=None
    except Exception as error:
        erro=type(error).__name__+': '+str(error)
    finally:
        atividade['tipo_etapa_id']=original
        del ctrl.sap.showEndActivityDialog
    return {'erro':erro,'avisos':[m['texto'] for m in log['mensagens'][before:]],'dialogo':[list(a) for a in dialogo]}


def mensagensDaGuarda(layer):
    from SAP_Operador.modules.versionamento.campo import GuardaDeCampo
    out=[]
    for child in layer.findChildren(GuardaDeCampo):
        out+=child.mensagens
    return out


def recusa(pacoteRemoto,project,iface):
    """Pacote local de um SAP Gerente antigo: tipo 2, 3 ou o tipo 4 sem a seção
    versionamento. O plugin anterior aceitava o login e abria as camadas do
    banco local pelo PostGIS."""
    from qgis.core import QgsVectorLayer
    def pacoteLocal(numero,versionamento=None):
        pacote=json.loads(json.dumps(pacoteRemoto))
        pacote['dados'].pop('login_info',None)
        if numero is None: pacote['dados']['atividade']['dado_producao'].pop('tipo_dado_producao_id',None)
        else: pacote['dados']['atividade']['dado_producao']['tipo_dado_producao_id']=numero
        if versionamento: pacote['dados']['atividade']['versionamento']=versionamento
        pacote['local_db']={'alias':'local','database':'producao_local','host':'localhost','port':'5432','username':'operador'}
        pacote['dados']['atividade']['monitoramento']=[]
        return pacote
    variantes=[('tipo 2',pacoteLocal(2),'tipo 2'),('tipo 3',pacoteLocal(3),'tipo 3'),
               ('tipo 4 sem a seção versionamento',pacoteLocal(4),'não enviou a base versionada')]
    resultados={}
    for nome,pacote,trecho in variantes:
        ctrl=controlador(pacote,iface)
        before=len(log['mensagens'])
        try:
            ok=ctrl.authUser('operador','senha','localhost','5432','sap_local'); erro=None
        except Exception as error:
            ok=None; erro=type(error).__name__+': '+str(error)
        textos=[m['texto'] for m in log['mensagens'][before:] if m['tipo']=='critical']
        resultados[nome]={'login':ok,'erro':erro,'mensagens':textos}
        check('login local recusado, '+nome+': sem exceção e com o motivo',
              ok is False and erro is None and len(textos)==1 and trecho in textos[0] and 'base versionada' in textos[0],resultados[nome])
        # O painel, se pedido mesmo assim, não monta.
        before=len(log['mensagens'])
        try:
            dock=ctrl.loadDockWidget('operador',SENHA_LOCAL,'localhost','5432','sap_local'); erro=None
        except Exception as error:
            dock=None; erro=type(error).__name__+': '+str(error)
        check('painel do modo local não monta, '+nome,dock is None and erro is None and ctrl.sapActivity is None and
              any(trecho in m['texto'] for m in log['mensagens'][before:]),(erro,log['mensagens'][before:]))
    log['recusas']=resultados
    vetores=[l.name() for l in project.mapLayers().values() if isinstance(l,QgsVectorLayer)]
    check('nenhuma camada, nenhum processing e nenhum pedido de rede nas recusas',
          not vetores and not log['processing'] and not log['rede'],(vetores,[p['alg'] for p in log['processing']],log['rede']))
    # Controle: sem o tipo e com a base versionada, o login passa.
    controle=pacoteLocal(None,{'repo_id':str(uuid.uuid4()),'papel':'atividade','datasets':[],'arquivo':'x.gpkg','sha256':'0'*64})
    ctrl=controlador(controle,iface)
    before=len(log['mensagens'])
    check('controle: pacote local sem o tipo e com a base versionada aceito no login',
          ctrl.authUser('operador','senha','localhost','5432','sap_local') is True and not log['mensagens'][before:],log['mensagens'][before:])


def defeitosDoModoLocal(ctrl,dock,pacote):
    """Defeitos do modo local achados na onda 2 (contrato-sap.md, 10.4)."""
    import ast
    import inspect
    from SAP_Operador.modules.sap.dataModels import sapActivityLocal
    # 1. reload refaz o painel do modo local com o pacote já lido (antes:
    # getActivity() sem o pacote e makeRemoteProductionToolsDock(self, painel),
    # com o painel no lugar do `sap`).
    chamadas=[]
    factory=ctrl.guiFactory
    for nome in ('makeLocalProductionToolsDock','makeRemoteProductionToolsDock'):
        original=getattr(factory,nome)
        def espiao(*args,_nome=nome,_original=original,**kwargs):
            chamadas.append((_nome,args[1:] if args and args[0] is ctrl else args))
            return _original(*args,**kwargs)
        setattr(factory,nome,espiao)
    try:
        ctrl.reload(); erro=None
    except Exception as e:
        erro=''.join(traceback.format_exception(type(e),e,e.__traceback__))[-800:]
    check('reload refaz o painel do modo local com o pacote lido',
          erro is None and [c[0] for c in chamadas]==['makeLocalProductionToolsDock'] and chamadas[0][1]==(dock,) and
          ctrl.productionTools is dock and ctrl.sapActivity.getId()==pacote['dados']['atividade']['id'],
          (erro,[(n,[type(a).__name__ for a in a_]) for n,a_ in chamadas]))
    # 2. O usuário da atividade do SAP 3.0 é usuario_uuid (o pacote não tem usuario_id).
    try:
        valor=ctrl.sapActivity.getLayerDefaultFieldValue()[0]['atributos'][0]['valor']; erro=None
    except Exception as e:
        valor=None; erro=type(e).__name__+': '+str(e)
    check('usuário da atividade local lido de usuario_uuid',
          valor==pacote['dados']['usuario_uuid'] and 'usuario_id' not in pacote['dados'],(valor,erro))
    # 3. Método morto: getScale definido duas vezes, e só o segundo vale.
    arvore=ast.parse(inspect.getsource(sapActivityLocal))
    classe=next(n for n in arvore.body if isinstance(n,ast.ClassDef) and n.name=='SapActivityLocal')
    nomes=[n.name for n in classe.body if isinstance(n,ast.FunctionDef)]
    repetidos=sorted({n for n in nomes if nomes.count(n)>1})
    # 4. Tipo de produto do SAP 3.0: `subtipo_produto` (o pacote não tem `tipo_produto`).
    atividade=pacote['dados']['atividade']
    check('tipo de produto da atividade local lido de subtipo_produto, como no remoto',
          ctrl.sapActivity.getProductType()==atividade['subtipo_produto']=='Carta topográfica' and 'tipo_produto' not in atividade and
          ctrl.getProductType()==atividade['subtipo_produto'],(ctrl.sapActivity.getProductType(),sorted(k for k in atividade if 'produto' in k)))
    check('SapActivityLocal sem método repetido (morto)',not repetidos and ctrl.sapActivity.getScale()=='1:25000',
          (repetidos,ctrl.sapActivity.getScale()))


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

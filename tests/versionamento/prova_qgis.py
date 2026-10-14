"""Prova do SAP Operador com o versionamento, no QGIS 4 real e sem interface.

Roda o plugin de verdade (controladores, provedor `dsgversioning`, algoritmos
reais do DsgTools) contra o servidor falso deste diretório. Nenhum sistema
real é tocado: o servidor sobe no loopback, em porta livre, só durante a prova.

Uso (Windows, QGIS 4.0.0):
    set QT_QPA_PLATFORM=offscreen
    set DSGTOOLS_PATH=<pasta que contém o pacote DsgTools>
    "<QGIS>\\bin\\python-qgis.bat" prova_qgis.py <cenario> <saida.json> [<pasta que contém o pacote SAP_Operador>]

Cenários:
- `versionado`: carrega a atividade do tipo 4 pelo provedor, confere
  `uri().schema()/table()`, domínios do modelo, estilos, apelidos, ações,
  regras de formatação, temas e estatística de regras (algoritmos reais do
  DsgTools, sem mudança neles), o filtro de subfase, a leitura pela página
  DSGP/1, edita e salva, recebe recusa por campo (`permission`), desfaz,
  divide, funde, lê o histórico e finaliza com 409, resolve o conflito na tela
  e finaliza de novo.
- `tipo2`: carrega uma atividade do tipo 2 (PostGIS fictício) com o
  `processing.run` gravado; a saída é o rastro das chamadas, que tem de ser
  IGUAL ao do HEAD (compare os dois JSON).

Sem o terceiro argumento, o plugin é o deste repositório. Para reprovar o
estado anterior, extraia o HEAD (`git archive HEAD`) numa pasta chamada
SAP_Operador e passe a pasta-mãe dela.
"""
import json
import os
import sys
import traceback
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

HERE=Path(__file__).resolve().parent
SCENARIO=sys.argv[1]
OUTPUT=Path(sys.argv[2])
PLUGIN_PARENT=Path(sys.argv[3]).resolve() if len(sys.argv)>3 else HERE.parents[2]

from qgis.core import QgsApplication  # noqa: E402

app=QgsApplication([],True)
app.initQgis()

log={'cenario':SCENARIO,'plugin':str(PLUGIN_PARENT.name),'checks':{},'processing':[],'mensagens':[]}


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
    from qgis.core import QgsProject,QgsVectorLayer,QgsFeature,QgsGeometry,Qgis,QgsDataSourceUri
    from qgis.PyQt import QtWidgets
    sys.path.insert(0,os.path.join(QgsApplication.prefixPath(),'python','plugins'))
    from processing.core.Processing import Processing
    Processing.initialize()
    dsgtools=os.environ.get('DSGTOOLS_PATH')
    if not dsgtools: raise SystemExit('Defina DSGTOOLS_PATH (pasta que contém o pacote DsgTools).')
    sys.path.insert(0,dsgtools)
    from DsgTools.core.DSGToolsProcessingAlgs.dsgtoolsProcessingAlgorithmProvider import DSGToolsProcessingAlgorithmProvider
    dsgProvider=DSGToolsProcessingAlgorithmProvider()
    QgsApplication.processingRegistry().addProvider(dsgProvider)

    # Caixas de mensagem modais não bloqueiam a prova: viram registro.
    def note(kind):
        def show(parent,title,text,*args,**kwargs):
            log['mensagens'].append({'tipo':kind,'titulo':title,'texto':str(text)})
            return QtWidgets.QMessageBox.StandardButton.Ok
        return show
    for kind in ('critical','information','warning'):
        setattr(QtWidgets.QMessageBox,kind,staticmethod(note(kind)))
    QtWidgets.QMessageBox.question=staticmethod(lambda *a,**k:QtWidgets.QMessageBox.StandardButton.Yes)

    import servidor_falso
    server,estado,url=servidor_falso.iniciar(SCENARIO)

    import processing
    realRun=processing.run
    project=QgsProject.instance()

    def layerName(value):
        layer=project.mapLayer(value) if isinstance(value,str) else None
        return 'camada:'+layer.name() if layer is not None else value

    def normalize(value):
        if isinstance(value,dict): return {k:normalize(v) for k,v in value.items() if k!='FME_MANAGER' or True}
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
        entry={'alg':algorithmId,'params':normalize(parameters)}
        log['processing'].append(entry)
        if algorithmId=='dsgtools:loadlayersfrompostgisalgorithm':
            return fakePostgis(parameters)
        if SCENARIO=='tipo2' and algorithmId=='dsgtools:grouplayers':
            # Sem banco as camadas são inválidas e o processing as recusa: o
            # grupo raiz com o nome do banco, de que o resto depende, nasce aqui.
            root=project.layerTreeRoot()
            for source in parameters['INPUT_LAYERS']:
                name=QgsDataSourceUri(source).database()
                if name and root.findGroup(name) is None: root.addGroup(name)
            return {'OUTPUT':[]}
        if SCENARIO=='tipo2':
            # Sem banco: o rastro é a prova; o algoritmo não roda.
            return {'OUTPUT':'' if algorithmId=='dsgtools:rulestatistics' else None}
        return realRun(algorithm,parameters,*args,**kwargs)
    processing.run=recordingRun

    from SAP_Operador.modules.qgis.qgisApi import QgisApi
    from SAP_Operador.modules.sap.controllers.remoteSapCtrl import RemoteSapCtrl
    from SAP_Operador.controllers.remoteProdToolsDockCtrl import RemoteProdToolsDockCtrl
    from SAP_Operador.modules.dsgTools.factories.processingQgisFactory import ProcessingQgisFactory

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
        def getAttributeValueMap(self,name,schema):
            return {'tipo_massa_dagua':{'Lago (1)':1}} if name=='cobter_massa_dagua_a' else {}

    class Tools:
        def getTool(self,name,controller):
            log.setdefault('ferramentas',[]).append(name)
            return Recorder(name)

    qgisApi=QgisApi(); qgisApi.load=lambda:None
    # A ação "Mostrar feição" pede a janela principal como QObject pai; o iface
    # simulado não é um. Fica registrada a chamada, igual nos dois cenários.
    qgisApi.loadLayerActions=lambda layerIds:log.setdefault('acoes_de_camada',[]).append(sorted(layerName(i) for i in layerIds))
    try:
        from SAP_Operador.modules import versionamento
        versionamento.registrar(iface)
        log['registro']='modules.versionamento.registrar'
    except ImportError as error:
        log['registro']='ausente: '+str(error)
    sap=RemoteSapCtrl(qgisApi)
    ctrl=RemoteProdToolsDockCtrl(sap=sap,qgis=qgisApi,databaseFactory=Database(),processingFactoryDsgTools=ProcessingQgisFactory(),
                                 fme=Recorder('fme'),prodToolsSettings=Recorder('settings'),toolFactoryDsgTools=Tools())
    check('login',ctrl.authUser(servidor_falso.USER,'senha-de-teste',url))
    ctrl.sapActivity=sap.getActivity()
    check('pacote lido',ctrl.sapActivity is not None)
    ctrl.loadActivityLayers()
    layers={layer.name():layer for layer in project.mapLayers().values() if isinstance(layer,QgsVectorLayer) and layer.name()!='moldura'}
    log['camadas']={name:{'provedor':layer.providerType(),'valida':layer.isValid(),'fonte_tem_service':'service=' in layer.source()}
                    for name,layer in layers.items()}
    if SCENARIO=='tipo2':
        check('nenhum pedido ao versionamento',not [p for p in estado.pedidos if p['path'].startswith(servidor_falso.SERVICE)])
        return
    versionado(ctrl,sap,estado,layers,iface,project)


def versionado(ctrl,sap,estado,layers,iface,project):
    from qgis.core import QgsFeature,QgsFeatureRequest,QgsGeometry,Qgis,QgsVectorLayer
    from qgis.PyQt import QtWidgets
    import servidor_falso
    from SAP_Operador.modules.versionamento import camadas, painel, provider as versioning, feature_page

    servidor_falso.checar_codificador(feature_page.decode)
    check('codificador DSGP/1 do servidor falso lido pelo decodificador do plugin',True)
    algs=[p['alg'] for p in log['processing']]
    check('sem LoadLayersFromPostgis',not any('postgis' in a for a in algs),algs)
    cobter=layers.get('cobter_massa_dagua_a'); revisao=layers.get('aux_revisao_p')
    check('camadas abertas pelo provedor',cobter is not None and revisao is not None and cobter.providerType()=='dsgversioning' and cobter.isValid(),
          {n:(l.providerType(),l.isValid()) for n,l in layers.items()})
    uri=cobter.dataProvider().uri()
    check('uri().schema() e uri().table() preenchidos',(uri.schema(),uri.table())==('edgv','cobter_massa_dagua_a'),(uri.schema(),uri.table(),cobter.source()))
    check('tabelaDaCamada',camadas.tabelaDaCamada(cobter)==('edgv','cobter_massa_dagua_a'))
    check('três feições lidas',cobter.featureCount()==3 and len(list(cobter.getFeatures()))==3,cobter.featureCount())
    binary=[p for p in estado.pedidos if p['path'].endswith('/features') and p['query'].get('format')=='dsgp1']
    check('leitura pela página DSGP/1',len(binary)>0,len(binary))
    service=[p for p in estado.pedidos if p['path'].startswith(servidor_falso.SERVICE)]
    check('Bearer do SAP em todo pedido ao repasse',all(p['authorization']=='Bearer '+estado.token for p in service),len(service))
    check('sem X-Dsg-Actor do cliente',all(p['actor_header'] is None for p in service))
    tipo=cobter.fields().indexFromName('tipo_massa_dagua')
    setup=cobter.editorWidgetSetup(tipo)
    check('domínio do modelo no formulário (ValueMap)',setup.type()=='ValueMap' and 'Lago (1)' in json.dumps(setup.config(),ensure_ascii=False),
          [setup.type(),setup.config()])
    check('nenhum mapa de valores do PostgreSQL',not log.get('banco') and 'dsgtools:assignvaluemaptolayersalgorithm' not in algs,log.get('banco'))
    check('estilo do pacote',cobter.styleManager().currentStyle()=='padrao',cobter.styleManager().styles())
    alias=cobter.attributeAlias(cobter.fields().indexFromName('nome'))
    check('apelido pelo DsgTools (casa por uri().table())',alias=='Nome da massa d água',alias)
    actions=[a.name() for a in cobter.actions().actions()]
    check('ação pelo DsgTools (casa por uri().table())','Doc MGCP' in actions,actions)
    styles=cobter.conditionalStyles().fieldStyles('tipo_massa_dagua')
    check('regras de formatação no versionado (pelo plugin)',len(styles)==1 and cobter.fields().indexFromName('attribute_error_description')>=0,
          [s.rule() for s in styles])
    check('algoritmo de formatação do DsgTools não chamado no versionado','dsgtools:assignformatrulestolayersalgorithm' not in algs)
    errors=[f['attribute_error_description'] for f in cobter.getFeatures()]
    check('campo virtual das regras calcula',sorted(errors)==['','','Tipo de massa d água vazio'],errors)
    themes=project.mapThemeCollection().mapThemes()
    check('tema pelo DsgTools (casa por uri().schema()/table())','Hidrografia' in themes and cobter.id() in project.mapThemeCollection().mapThemeVisibleLayerIds('Hidrografia'),themes)
    from SAP_Operador.modules.dsgTools.factories.processingQgisFactory import ProcessingQgisFactory
    statistics=ProcessingQgisFactory().createProcessing('RuleStatistics',ctrl).run({'rules':ctrl.sapActivity.getRules()[0]['regra'],'layers':ctrl.sapActivity.getLayers()})
    flat=json.dumps(statistics,ensure_ascii=False)
    check('estatística de regras do DsgTools acha a camada versionada','cobter_massa_dagua_a' in flat,statistics)
    log['estatistica']=statistics
    gaps=getattr(ctrl,'versioningGaps',{})
    check('subfase vira expressão QGIS',[l['filter'] for l in ctrl.sapActivity.getLayers() if l['nome']=='aux_revisao_p']==['"subfase_id" = \'7\''])
    subfase='"subfase_id" = \'7\''
    check('filtro de subfase aplicado pelo provedor (setSubsetString)',not gaps.get('unfiltered') and revisao.subsetString()==subfase,
          (gaps,revisao.subsetString()))
    check('filtro de subfase: só o apontamento da subfase',[f['descricao'] for f in revisao.getFeatures()]==['da subfase'] and revisao.featureCount()==1,
          ([f['descricao'] for f in revisao.getFeatures()],revisao.featureCount()))
    others=[row[0] for row in revisao.dataProvider()._cache.db.execute('SELECT f.fid FROM features f WHERE f.subfase_id=8')]
    check('filtro de subfase: feição de outra subfase não sai nem pelo fid',
          len(others)==1 and not list(revisao.getFeatures(QgsFeatureRequest(others[0]))) and
          [f['descricao'] for f in revisao.dataProvider().getFeatures(QgsFeatureRequest().setFlags(Qgis.FeatureRequestFlag.NoGeometry)
                                                                      .setSubsetOfAttributes(['descricao'],revisao.fields()))]==['da subfase'],others)
    pages=[p for p in estado.pedidos if p['path'].endswith('/features') and p['query'].get('dataset')=='aux_revisao_p']
    check('filtro de subfase: leitura pela página DSGP/1, sem filtro no pedido ao serviço',
          pages and all(p['query'].get('format')=='dsgp1' for p in pages) and
          not any(k in p['query'] for p in pages for k in ('sql','filter','subset','where')),[p['query'] for p in pages])
    reopened=QgsVectorLayer(revisao.source(),'reaberta','dsgversioning')
    check('filtro de subfase: o endereço guarda o filtro (projeto reaberto)',
          'sql=' in revisao.source() and reopened.subsetString()==subfase and reopened.featureCount()==1 and
          camadas.tabelaDaCamada(reopened)==('edgv','aux_revisao_p'),(revisao.source(),reopened.subsetString()))
    del reopened
    check('filtro inválido recusado, o anterior fica',not revisao.setSubsetString('"campo_que_nao_existe" = 1') and
          not revisao.setSubsetString('"subfase_id" = ') and revisao.subsetString()==subfase)
    # Endereço antigo (urlencode): o provedor ainda lê, e é ele que o DsgTools não casaria.
    from urllib.parse import urlencode
    oldUri=urlencode({'service':versioning.parse_uri(cobter.source())['service'],'repo':estado.atividade,'dataset':'cobter_massa_dagua_a'})
    old=QgsVectorLayer(oldUri,'antigo','dsgversioning')
    check('endereço antigo ainda abre',old.isValid() and old.featureCount()==3)
    check('endereço antigo: uri().table() vazio, tabelaDaCamada pelo dataset',
          old.dataProvider().uri().table()=='' and camadas.tabelaDaCamada(old)==('','cobter_massa_dagua_a'),
          (old.dataProvider().uri().table(),camadas.tabelaDaCamada(old)))
    del old

    # Editar e salvar -------------------------------------------------------------
    before=estado.generation
    target=next(f for f in cobter.getFeatures() if f['dsg_id']==estado.f2)
    check('editar',cobter.startEditing())
    cobter.changeAttributeValue(target.id(),cobter.fields().indexFromName('nome'),'Lago B renomeado')
    cobter.changeAttributeValue(target.id(),tipo,2)
    added=QgsFeature(cobter.fields())
    for index in range(cobter.fields().count()):
        value=cobter.dataProvider().defaultValue(index)
        if value is not None: added.setAttribute(index,value)
    added.setAttribute(cobter.fields().indexFromName('nome'),'Lago novo'); added.setAttribute(tipo,1)
    added.setGeometry(QgsGeometry.fromWkt('POLYGON((-50.94 -30,-50.93 -30,-50.93 -29.99,-50.94 -29.99,-50.94 -30))'))
    check('adicionar',cobter.addFeature(added))
    committed=cobter.commitChanges(False)
    check('salvar',committed,cobter.commitErrors())
    saves=[p for p in estado.pedidos if p['method']=='POST' and p['path'].endswith('/features')]
    check('um POST /features por salvamento',len(saves)==1,len(saves))
    body=saves[-1]['body']
    check('salvamento sem actor e com request_id','actor' not in body and bool(body.get('request_id')),sorted(body))
    stored=estado.features['cobter_massa_dagua_a'][estado.f2]['properties']
    check('relido no destino',stored['nome']=='Lago B renomeado' and stored['tipo_massa_dagua']==2 and estado.generation==before+1,stored)
    check('feição nova no destino',any(f['properties'].get('nome')=='Lago novo' for f in estado.features['cobter_massa_dagua_a'].values()))
    tracked=json.dumps(estado.microcontrole,ensure_ascii=False)
    check('microcontrole por feição com o nome da camada (tabelaDaCamada)','"camada": "cobter_massa_dagua_a"' in tracked,estado.microcontrole)

    # Recusa por campo ------------------------------------------------------------
    target=next(f for f in cobter.getFeatures() if f['dsg_id']==estado.f3)
    cobter.changeAttributeValue(target.id(),cobter.fields().indexFromName('nome'),'PROIBIDO')
    refused=cobter.commitChanges(False)
    found=cobter.dataProvider().last_violations
    check('recusa por campo: salvamento recusado',not refused and estado.features['cobter_massa_dagua_a'][estado.f3]['properties']['nome']=='Lago C')
    check('recusa por campo: código permission',[v.get('code') for v in found]==['permission'] and found[0]['field']=='nome',found)
    reports=versioning_reports()
    last=reports.last if reports else None
    check('aviso de salvamento com as recusas',last is not None and last[1]=='refused' and last[3]==found and 'permission' in last[2],last)
    dialog=painel.ViolationsDialog(None,'cobter',found)
    check('tabela de recusas por campo',dialog.table.rowCount()==1 and dialog.table.item(0,3).text()=='permission' and dialog.table.item(0,2).text()=='nome')
    cobter.rollBack()

    # Desfazer, dividir, fundir, histórico ----------------------------------------------
    serviceBase=ctrl.getVersioningServiceBase()
    client=painel.connection_for(serviceBase).client
    result=painel.undo_last_save(client,serviceBase,estado.atividade)
    check('desfazer último salvamento',estado.features['cobter_massa_dagua_a'][estado.f2]['properties']['nome']=='Lago B' and
          not any(f['properties'].get('nome')=='Lago novo' for f in estado.features['cobter_massa_dagua_a'].values()),result)
    check('camada relida depois do desfazer',sorted(f['nome'] for f in cobter.getFeatures())==['Lago A','Lago B','Lago C'])
    iface.activeLayer.return_value=cobter
    panel=painel.VersioningPanel(None,iface,serviceBase,ctrl.sapActivity.getVersioning())
    check('botão de atualizar com o bloco escondido (sem rota no SAP)',panel.pull.isHidden())
    target=next(f for f in cobter.getFeatures() if f['dsg_id']==estado.f1)
    cobter.selectByIds([target.id()])
    panel.split('LINESTRING(-50.995 -30.01,-50.995 -29.98)','divisão de teste')
    check('dividir',estado.f1 not in estado.features['cobter_massa_dagua_a'] and len(estado.lineage.get(estado.f1,{}).get('successors',[]))==2,panel.notice.text())
    pieces=[f for f in cobter.getFeatures() if f['dsg_id'] in estado.lineage[estado.f1]['successors']]
    check('partes relidas na camada',len(pieces)==2)
    cobter.selectByIds([f.id() for f in pieces])
    panel.fuse(pieces[0]['dsg_id'],'fusão de teste')
    fused=estado.lineage[pieces[0]['dsg_id']]['successors'][0]
    check('fundir',fused in estado.features['cobter_massa_dagua_a'] and pieces[0]['dsg_id'] not in estado.features['cobter_massa_dagua_a'],panel.notice.text())
    lineageBodies=[p['body'] for p in estado.pedidos if '/lineage/' in p['path']]
    check('linhagem sem actor',all('actor' not in b for b in lineageBodies) and len(lineageBodies)==2)
    target=next(f for f in cobter.getFeatures() if f['dsg_id']==estado.f2)
    cobter.selectByIds([target.id()])
    history=panel.history(show=False)
    check('histórico da feição',history.table.rowCount()>=2,history.table.rowCount())

    # Finalizar com 409 e resolver ------------------------------------------------------
    chosen={}
    def run(dialog):
        dialog.table.selectRow(0)
        chosen['item']=dialog.current()
        dialog.decide('mine',reason='o meu vale',ask=False)
        chosen['pendentes']=dialog.pending
        return QtWidgets.QDialog.DialogCode.Accepted
    painel.ConflictDialog.exec=run
    message=sap.endActivity({'atividade_id':101,'sem_correcao':False})
    check('finaliza: 409, tela de conflito e segunda chamada',len(estado.finalizacoes)==2 and 'finalizada' in message,(len(estado.finalizacoes),message))
    sessionCalls=[p['path'] for p in estado.pedidos if '/sessions/' in p['path']]
    check('sessão do merge lida no repositório que o 409 diz (o pai)',sessionCalls and all('/repos/'+estado.bloco+'/' in p for p in sessionCalls),sessionCalls)
    decision=estado.decisoes[-1]
    check('resolvido com o meu (origem)',decision['result']['properties']['nome']=='Lago A da atividade' and decision['delete'] is False
          and 'actor' not in decision and decision['reason']=='o meu vale',decision)
    check('sem conflito pendente depois',chosen.get('pendentes')==0)
    # Conflito do PULL: a sessão mora no próprio clone, e o 409 diz o repo_id dele.
    before=len(estado.pedidos); estado.sessao_repo=estado.atividade; estado.items[0]['status']='conflict'
    painel.ConflictDialog.exec=run
    message=sap.endActivity({'atividade_id':101,'sem_correcao':False})
    pullCalls=[p['path'] for p in estado.pedidos[before:] if '/sessions/' in p['path']]
    check('sessão do pull lida no próprio clone (repo_id do 409 igual ao do pacote)',
          pullCalls and all('/repos/'+estado.atividade+'/' in p for p in pullCalls) and 'finalizada' in message and estado.items[0]['status']=='resolved',
          (pullCalls,message))
    estado.sessao_repo=estado.bloco
    from SAP_Operador.modules.versionamento.painel import ConflictPayload
    check('sem repo_id no 409, a sessão é a do pai (status.parent_id)',
          painel.session_repository(client,estado.atividade,ConflictPayload({'dados':{'sessao_id':estado.sessao}}))==estado.bloco)
    # Fechar a tela sem resolver mantém a atividade e diz por quê.
    estado.items[0]['status']='conflict'
    painel.ConflictDialog.exec=lambda dialog:QtWidgets.QDialog.DialogCode.Rejected
    try:
        sap.endActivity({'atividade_id':101,'sem_correcao':False}); kept=False
    except Exception as error:
        kept='continua em execução' in str(error)
    check('fechar a tela de conflito mantém a atividade em execução',kept)

    # Botão "Versionamento" no quadro da atividade -----------------------------------
    from SAP_Operador.widgets.activityInfo import ActivityInfo
    ctrl.qgis.getMainWindow=lambda:None
    info=ActivityInfo(ctrl); info.setButtons()
    check('botão Versionamento visível na atividade versionada',not info.versioningButton.isHidden())
    info.versioningButton.click()
    check('botão abre o painel do versionamento',isinstance(getattr(ctrl,'versioningPanel',None),painel.VersioningPanel))

    # Projeto reaberto: a camada abre antes do login e volta depois dele -------------
    source=cobter.source()
    with versioning._connections_lock: versioning._connections.clear()
    again=QgsVectorLayer(source,'reaberta','dsgversioning'); project.addMapLayer(again)
    check('sem conexão, a camada reaberta fica inválida',not again.isValid())
    reopened=ctrl.reconnectVersionedLayers()
    check('depois do login a camada reabre',again.id() in reopened and again.isValid() and again.featureCount()>0,reopened)


def versioning_reports():
    from SAP_Operador.modules import versionamento
    return versionamento._state.get('reports')


if __name__=='__main__':
    status=0
    try:
        main()
    except BaseException as error:
        status=1
        log['erro']=''.join(traceback.format_exception(type(error),error,error.__traceback__))[-4000:]
    finally:
        OUTPUT.write_text(json.dumps(log,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        print(json.dumps({'cenario':SCENARIO,'status':'ok' if status==0 else 'falhou','checks':sum(1 for c in log['checks'].values() if c['ok']),
                          'erro':(log.get('erro') or '').strip().splitlines()[-1:] },ensure_ascii=False),flush=True)
        os._exit(status)

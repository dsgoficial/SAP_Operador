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
  DSGP/1, a grade de revisão gravada pelo provedor (com a recusa da etapa
  mostrada antes), a lista de rotinas sem FME (com e sem a chave `fme` na
  resposta do servidor), o insumo de banco PostGIS recusado, edita e salva,
  recebe recusa por campo (`permission`), desfaz, divide, funde, lê o
  histórico e finaliza com 409, resolve o conflito na tela e finaliza de novo.
  O pacote é lido com `tipo_dado_producao_id` = 4 e depois sem ele, sem
  `configuracao_producao` e sem `login_info` (o servidor 3.38.0 em diante), e
  a senha do SAP não entra no pacote.
- `recusa`: o servidor antigo manda atividade do tipo 2 (PostGIS fictício),
  3, 1, ou do tipo 4 sem a seção `versionamento`. O plugin (4.4.0, só a base
  versionada) recusa cada uma com o motivo, sem exceção, sem painel, sem
  camada e sem chamada de processing, ao abrir a atividade, no projeto
  reaberto, pelo outro plugin (`loadDockWidgetExternally`) e no
  carregamento; o pacote sem o tipo e com a base versionada é aceito.

Sem o terceiro argumento, o plugin é o deste repositório. Para reprovar o
estado anterior, extraia o HEAD (`git archive HEAD`) numa pasta chamada
SAP_Operador e passe a pasta-mãe dela.
"""
import inspect
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
        if isinstance(value,dict): return {k:normalize(v) for k,v in value.items()}
        if isinstance(value,list): return [normalize(v) for v in value]
        if isinstance(value,str): return layerName(value)
        return value

    def recordingRun(algorithm,parameters,*args,**kwargs):
        algorithmId=algorithm if isinstance(algorithm,str) else algorithm.id()
        entry={'alg':algorithmId,'params':normalize(parameters)}
        log['processing'].append(entry)
        if SCENARIO=='recusa':
            # Nada deve chegar aqui; o rastro é a prova, e o algoritmo não roda
            # (o plugin anterior pediria o banco fictício).
            return {'OUTPUT':[]}
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

    from SAP_Operador.modules.dsgTools.toolbarLaunchers.reviewToolbar import ReviewToolBar

    class ReviewToolBarDaProva(ReviewToolBar):
        # O ReviewToolBar do plugin (grava a grade nova na camada); só a barra
        # do DsgTools, que pede a interface, é trocada por um registro.
        def getTool(self):
            class Barra:
                def setState(self,**kwargs):
                    log.setdefault('revisao',[]).append({k:(v.name() if hasattr(v,'name') else v) for k,v in kwargs.items()})
            return Barra()

    class Tools:
        def getTool(self,name,controller):
            log.setdefault('ferramentas',[]).append(name)
            if name=='ReviewToolBar' and SCENARIO=='versionado':
                return ReviewToolBarDaProva(controller)
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
    kwargs=dict(sap=sap,qgis=qgisApi,processingFactoryDsgTools=ProcessingQgisFactory(),
                prodToolsSettings=Recorder('settings'),toolFactoryDsgTools=Tools())
    parameters=inspect.signature(RemoteProdToolsDockCtrl.__init__).parameters
    if 'databaseFactory' in parameters:
        kwargs['databaseFactory']=Database()  # plugin anterior à 4.4.0, para reprovar o estado anterior
    if 'fme' in parameters:
        kwargs['fme']=Recorder('fme')  # plugin anterior à 4.3.0, para reprovar o estado anterior
    ctrl=RemoteProdToolsDockCtrl(**kwargs)
    check('login',ctrl.authUser(servidor_falso.USER,'senha-de-teste',url))
    if SCENARIO=='recusa':
        recusa(ctrl,sap,estado,project,qgisApi)
        return
    ctrl.sapActivity=sap.getActivity()
    check('pacote lido (tipo 4 em dado_producao)',ctrl.sapActivity is not None and
          ctrl.sapActivity.getData()['dados']['atividade']['dado_producao'].get('tipo_dado_producao_id')==4)
    check('a senha e o login do SAP não entram no pacote da atividade',
          'senha' not in ctrl.sapActivity.getData() and 'login' not in ctrl.sapActivity.getData(),sorted(ctrl.sapActivity.getData()))
    # O servidor 3.38.0 mantém o tipo 4 por uma versão e não manda mais
    # login_info nem configuracao_producao: o plugin não depende desses campos.
    def semTipo(dados):
        dados['atividade']['dado_producao'].pop('tipo_dado_producao_id',None)
        dados['atividade']['dado_producao'].pop('configuracao_producao',None)
        dados.pop('login_info',None)
        return dados
    estado.ajuste=semTipo
    before=len(log['mensagens'])
    ctrl.sapActivity=sap.getActivity()
    check('pacote sem tipo_dado_producao_id, configuracao_producao e login_info aceito',
          ctrl.sapActivity is not None and ctrl.sapActivity.getData()['dados']['atividade']['dado_producao']=={} and
          'login_info' not in ctrl.sapActivity.getData()['dados'] and not log['mensagens'][before:],
          (ctrl.sapActivity.getData()['dados']['atividade'].get('dado_producao') if ctrl.sapActivity else None,log['mensagens'][before:]))
    # A primeira carga cria a grade de revisão e a etapa a recusa no serviço;
    # a recusa tem de chegar ao operador (gradeDeRevisao).
    estado.recusar_grade=SCENARIO=='versionado'
    ctrl.loadActivityLayers()
    layers={layer.name():layer for layer in project.mapLayers().values() if isinstance(layer,QgsVectorLayer) and layer.name()!='moldura'}
    log['camadas']={name:{'provedor':layer.providerType(),'valida':layer.isValid(),'fonte_tem_service':'service=' in layer.source()}
                    for name,layer in layers.items()}
    versionado(ctrl,sap,estado,layers,iface,project)


def recusa(ctrl,sap,estado,project,qgisApi):
    """Servidor antigo: atividade de dado de produção que não é a base
    versionada (tipos 1, 2 e 3, ou o tipo 4 sem a seção `versionamento`). O
    plugin anterior aceitava e abria o banco (tipos 2 e 3) com a credencial."""
    from qgis.core import QgsVectorLayer
    import servidor_falso
    from SAP_Operador.modules.sap.controllers.remoteSapCtrl import RemoteSapCtrl

    def tipo(numero,semLogin=False,semConfiguracao=False,versionamento=False):
        def ajustar(dados):
            if numero is None: dados['atividade']['dado_producao'].pop('tipo_dado_producao_id',None)
            else: dados['atividade']['dado_producao']['tipo_dado_producao_id']=numero
            if semLogin: dados.pop('login_info',None)
            if semConfiguracao: dados['atividade']['dado_producao'].pop('configuracao_producao',None)
            if versionamento:
                dados['versionamento']={'repo_id':estado.atividade,'servico':servidor_falso.SERVICE,'papel':'atividade',
                                        'datasets':[{'schema':'edgv','nome':n,'dataset':n} for n in estado.specs]}
            return dados
        return ajustar

    def criticas(before):
        return [m['texto'] for m in log['mensagens'][before:] if m['tipo']=='critical']

    variantes=[
        ('tipo 2 (banco PostGIS com controle de permissões, com login_info)',tipo(2),'tipo 2'),
        ('tipo 3 (banco PostGIS, senha do SAP como credencial)',tipo(3,semLogin=True),'tipo 3'),
        ('tipo 1 (dado não controlado pelo SAP)',tipo(1,semLogin=True,semConfiguracao=True),'tipo 1'),
        ('tipo 4 sem a seção versionamento',tipo(4,semLogin=True,semConfiguracao=True),'não enviou a base versionada'),
    ]
    resultados={}
    for nome,ajuste,trecho in variantes:
        estado.ajuste=ajuste
        before=len(log['mensagens'])
        try:
            model=sap.getActivity(); erro=None
        except Exception as error:
            model=None; erro=type(error).__name__+': '+str(error)
        textos=criticas(before)
        resultados[nome]={'aceito':model is not None,'erro':erro,'mensagens':textos}
        check('recusa ao abrir a atividade, '+nome+': sem pacote, sem exceção e com o motivo',
              model is None and erro is None and len(textos)==1 and trecho in textos[0] and 'base versionada' in textos[0] and
              not qgisApi.getProjectVariable('productiontools:activityName'),resultados[nome])
    log['recusas']=resultados

    # O botão do plugin (login): o painel não monta, e nada quebra.
    estado.ajuste=tipo(2)
    before=len(log['mensagens'])
    try:
        dock=ctrl.loadDockWidget(); erro=None
    except Exception as error:
        dock=None; erro=type(error).__name__+': '+str(error)
    check('painel não monta para o tipo 2, sem exceção e com o motivo',
          dock is None and erro is None and ctrl.productionTools is None and len(criticas(before))==1,(erro,criticas(before)))

    # Projeto reaberto com a atividade do tipo 2 em execução: recusado.
    qgisApi.setProjectVariable('productiontools:activityName','Aquisição de hidrografia')
    before=len(log['mensagens'])
    try:
        valid=sap.isValidActivity(); erro=None
    except Exception as error:
        valid=None; erro=type(error).__name__+': '+str(error)
    check('projeto reaberto com atividade do tipo 2 recusado com o motivo',
          valid is False and erro is None and any('tipo 2' in t for t in criticas(before)),(valid,erro,criticas(before)))

    # O outro plugin entrega o pacote (main.startPluginExternally).
    externo=RemoteSapCtrl(qgisApi)
    externo.setupActivityDataModelExternally({'dados':estado.pacote()})
    before=len(log['mensagens'])
    try:
        dock=ctrl.loadDockWidgetExternally(externo.getActivityDataModel(),externo); erro=None
    except Exception as error:
        dock=None; erro=type(error).__name__+': '+str(error)
    check('pacote do tipo 2 entregue por outro plugin recusado, sem painel',
          dock is None and erro is None and any('tipo 2' in t for t in criticas(before)),(erro,criticas(before)))

    # Carregar camadas com o pacote do tipo 2 (nenhum caminho deve chegar aqui,
    # e se chegar não abre banco).
    ctrl.sapActivity=externo.getActivityDataModel()
    before=len(log['mensagens'])
    try:
        ctrl.loadActivityLayers(); erro=None
    except Exception as error:
        erro=type(error).__name__+': '+str(error)
    check('carregar camadas do tipo 2: nada carrega, sem exceção e com o motivo',
          erro is None and any('tipo 2' in t for t in criticas(before)),(erro,criticas(before)))

    vetores=[l.name() for l in project.mapLayers().values() if isinstance(l,QgsVectorLayer)]
    check('nenhuma camada, nenhum processing e nenhum pedido ao versionamento nas recusas',
          not vetores and not log['processing'] and not [p for p in estado.pedidos if p['path'].startswith(servidor_falso.SERVICE)],
          (vetores,[p['alg'] for p in log['processing']]))

    # Controle: sem o tipo (o servidor depois da 3.38.0) e com a base versionada, aceito.
    estado.ajuste=tipo(None,semLogin=True,semConfiguracao=True,versionamento=True)
    before=len(log['mensagens'])
    model=sap.getActivity()
    check('controle: pacote sem o tipo e com a base versionada aceito',
          model is not None and model.isVersioned() and not criticas(before),criticas(before))


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

    gradeDeRevisao(ctrl,estado,project)
    rotinasSemFme(ctrl)
    insumoPostgis(ctrl,project)

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
    saves=[p for p in estado.pedidos if p['method']=='POST' and p['path'].endswith('/features') and p['body'].get('dataset')=='cobter_massa_dagua_a']
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
    # No pull o lado do operador é o DESTINO (`ours`, o clone): "o meu" grava o
    # que a atividade gravou, e não o bloco.
    decision=estado.decisoes[-1]
    check('pull: "o meu" é o que a atividade gravou',decision['result']['properties']['nome']=='Lago A da atividade',decision)
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


def gradeDeRevisao(ctrl,estado,project):
    """Grade de revisão no versionado remoto: mora na classe aux_grid_revisao_a do
    clone da atividade e é gravada pelo provedor, pelas rotas do SAP."""
    from SAP_Operador.modules.versionamento import camadas, model as model_rules
    grid=next((l for l in project.mapLayers().values() if camadas.tabelaDaCamada(l)[1]=='aux_grid_revisao_a'),None)
    check('grade de revisão aberta pelo provedor, do clone da atividade',
          grid is not None and grid.providerType()=='dsgversioning' and grid.isValid() and
          grid.subsetString()=='unidade_trabalho_id = 55 AND etapa_id = 9',
          (grid.providerType() if grid else None,grid.subsetString() if grid else None,getattr(ctrl,'reviewGridGap',None)))
    # 1. A etapa recusa a grade (servidor falso, `recusar_grade`): o operador vê o
    # motivo, nada fica no buffer e a barra do DsgTools não é ligada.
    refused=[m for m in log['mensagens'] if m['tipo']=='critical' and 'grade de revisão não foi gravada' in m['texto']]
    check('grade recusada pelo serviço: motivo mostrado ao operador',
          refused and 'permission' in refused[-1]['texto'] and not grid.isEditable() and not grid.isModified() and
          not estado.features['aux_grid_revisao_a'] and not log.get('revisao'),
          ([m['texto'] for m in refused],grid.isEditable(),len(estado.features['aux_grid_revisao_a']),log.get('revisao')))
    # 2. Sem a recusa, a mesma ação grava a grade nova pelo provedor.
    estado.recusar_grade=False
    before=len(estado.pedidos)
    ctrl.loadReviewTool()
    posts=[p for p in estado.pedidos[before:] if p['method']=='POST' and p['path'].endswith('/features')]
    stored=list(estado.features['aux_grid_revisao_a'].values())
    check('grade nova gravada pelo provedor (POST /features do clone, pelo repasse do SAP)',
          len(posts)==1 and posts[0]['body']['dataset']=='aux_grid_revisao_a' and
          posts[0]['path']=='/api/versionamento/servico/repos/'+estado.atividade+'/features' and
          len(posts[0]['body'].get('inserts') or [])==len(stored)>0 and 'actor' not in posts[0]['body'],
          [(p['path'],p['body'].get('dataset'),len(p['body'].get('inserts') or [])) for p in posts])
    check('células da grade no destino: identidade, unidade de trabalho, etapa e posição',
          all(model_rules.is_canonical_uuid(f['id']) and f['properties']['unidade_trabalho_id']==55 and
              f['properties']['etapa_id']==9 and f['properties']['visited'] is False for f in stored) and
          sorted(f['properties']['rank'] for f in stored)==list(range(len(stored))) and
          all(f['properties']['atividade_id']==101 for f in stored),
          [f['properties'] for f in stored][:3])
    check('grade relida na camada (filtrada) e barra de revisão ligada nela',
          grid.featureCount()==len(stored) and not grid.isEditable() and
          log.get('revisao') and log['revisao'][-1]['layer']==grid.name() and log['revisao'][-1]['rankFieldName']=='rank',
          (grid.featureCount(),len(stored),log.get('revisao')))
    # 3. A barra do DsgTools marca a célula visitada pelo commit da camada.
    cell=next(iter(grid.getFeatures()))
    grid.startEditing(); grid.changeAttributeValue(cell.id(),grid.fields().indexOf('visited'),True)
    check('célula visitada gravada pelo provedor',grid.commitChanges() and
          estado.features['aux_grid_revisao_a'][cell['dsg_id']]['properties']['visited'] is True,grid.commitErrors())
    # 4. Recarregar a ferramenta com a grade cheia não cria outra.
    before=len(estado.pedidos)
    ctrl.loadReviewTool()
    check('grade cheia: a ferramenta não grava outra',
          not [p for p in estado.pedidos[before:] if p['method']=='POST'] and len(estado.features['aux_grid_revisao_a'])==len(stored))
    log['grade']={'celulas':len(stored),'filtro':grid.subsetString()}


def rotinasSemFme(ctrl):
    """O FME saiu do SAP 3.0 (4.3.0): a lista de rotinas da atividade traz só os
    modelos e as regras, sem quebrar, com a chave `fme` na resposta (o servidor
    de hoje) e sem ela (o servidor sem FME). O plugin anterior listava a rotina
    que o gerenciador devolvia e, sem a chave, dava KeyError."""
    atividade=ctrl.sapActivity.getData()['dados']['atividade']
    tinha='fme' in atividade; original=atividade.get('fme')
    rotina={'id':11,'rotina':'verifica_no_banco','descricao':'Verifica no banco','routineType':'fme','server':'http://fme.invalid',
            'parameters':['dbarea','sapsubfase'],'description':'verifica_no_banco: Verifica no banco'}

    class GerenciadorFalso:
        # Só o plugin anterior o consulta; responde como o gerenciador respondia.
        def getSapRoutines(self,config):
            return [dict(rotina)] if config else []
    ctrl.fme=GerenciadorFalso()
    esperado=[r.get('routineType') for r in ctrl.sapActivity.getQgisModels()+ctrl.sapActivity.getRuleRoutines()]
    resultados={}
    for nome,chave in (('com a chave fme',[{'servidor':'http://fme.invalid','rotina':'verifica_no_banco'}]),('sem a chave fme',None)):
        if chave is None: atividade.pop('fme',None)
        else: atividade['fme']=chave
        try:
            resultados[nome]={'tipos':[r.get('routineType') for r in ctrl.getActivityRoutines()],'erro':None}
        except Exception as error:
            resultados[nome]={'tipos':None,'erro':type(error).__name__+': '+str(error)}
    if tinha: atividade['fme']=original
    else: atividade.pop('fme',None)
    log['rotinas']=resultados
    for nome,resultado in resultados.items():
        check('rotinas da atividade '+nome+': só modelos e regras, sem erro',
              resultado['erro'] is None and resultado['tipos']==esperado,{'esperado':esperado,**resultado})
    check('nenhuma rotina FME disparada no cenário',
          not [p for p in log['processing'] if p['alg']=='dsgtools:runremotefme'])


def insumoPostgis(ctrl,project):
    """Insumo de banco PostGIS (tipo de insumo 3): até a 4.3.0 recebia a
    credencial do banco da atividade (na base versionada, None) e o carregamento
    tentava o banco. Agora o insumo vem como o SAP o manda e é recusado com o
    motivo, sem camada."""
    banco=[i for i in ctrl.getActivityInputs() if i['tipo_insumo_id']==3]
    check('insumo PostGIS sem a credencial do banco da atividade',
          len(banco)==1 and not any(k in banco[0] for k in ('usuario','senha','workUnitGeometry')),banco)
    before=set(project.mapLayers()); n=len(log['mensagens'])
    try:
        ctrl.loadActivityInputs([dict(banco[0])]); erro=None
    except Exception as error:
        erro=type(error).__name__+': '+str(error)
    textos=[m['texto'] for m in log['mensagens'][n:] if m['tipo']=='critical']
    check('insumo PostGIS recusado com o motivo, nada carregado',
          erro is None and len(textos)==1 and 'banco PostGIS' in textos[0] and 'insumo_banco' in textos[0] and set(project.mapLayers())==before,
          (erro,textos))


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

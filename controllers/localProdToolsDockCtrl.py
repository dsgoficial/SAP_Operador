
from collections import OrderedDict

from SAP_Operador.controllers.prodToolsCtrl import ProdToolsCtrl
from qgis import core, gui, utils

import os
import json

from SAP_Operador.postgresql import Postgresql
from SAP_Operador.modules.versionamento import camadas, campo
from SAP_Operador.modules.versionamento.regras import aplicarRegrasDeFormatacao, estatisticaDeRegras
from SAP_Operador.modules.sap.dataModels.sapActivityLocal import SapActivityLocal
from qgis.PyQt import QtWidgets
import psycopg2


class LocalProdToolsDockCtrl(ProdToolsCtrl):

    def __init__(
            self,
            sap,
            qgis,
            processingFactoryDsgTools,
            prodToolsSettings,
            toolFactoryDsgTools,
            pomodoro=None,
            guiFactory=None,
            spatialVerificationFactory=None,
            canvasMonitoring=None,
        ):
        super(LocalProdToolsDockCtrl, self).__init__(
            sap=sap,
            qgis=qgis,
            processingFactoryDsgTools=processingFactoryDsgTools,
            prodToolsSettings=prodToolsSettings,
            toolFactoryDsgTools=toolFactoryDsgTools,
            pomodoro=pomodoro,
            guiFactory=guiFactory,
            spatialVerificationFactory=spatialVerificationFactory,
            canvasMonitoring=canvasMonitoring,
        )

    def authUser(self, dbusername, dbpassword, dbhost, dbport, dbnam):
        pg = Postgresql(dbnam, dbusername, dbhost, dbport, dbpassword)
        try:
            pg.execute(
                '''
                    SELECT * FROM public.sap_local;
                ''',
                ()
            )
        except psycopg2.errors.UndefinedTable:
            raise Exception('Tabela "public.sap_local" não existe!')
        result = pg.execute(
            '''
                SELECT count(*) FROM public.sap_local;
            ''',
            ()
        )
        if result[0][0] == 0:
            raise Exception('Não há dados na tabela "public.sap_local"!')
        # O pacote local de dado de produção que não é a base versionada (de um
        # SAP Gerente antigo) é recusado no login, com o motivo, sem painel.
        reason = self.getUnsupportedReason(self.readLocalPackage(pg))
        if reason:
            self.showErrorMessageBox(self.qgis.getMainWindow(), 'Atividade não atendida', reason)
            return False
        return True

    def readLocalPackage(self, pg):
        # O pacote que o SAP Gerente grava em public.sap_local (json_atividade
        # em texto, ou já lido pelo psycopg2 numa coluna json).
        result = pg.execute(
            '''
                SELECT json_atividade FROM public.sap_local;
            ''',
            ()
        )
        activityData = result[0][0]
        if isinstance(activityData, (str, bytes)):
            activityData = json.loads(activityData)
        return activityData

    def getUnsupportedReason(self, activityData):
        candidate = SapActivityLocal()
        candidate.setData(activityData)
        return candidate.getUnsupportedReason()

    def reload(self):
        #self.prodToolsSettings.checkPluginUpdates()
        if self.productionTools is None:
            return
        self.removeDock()
        # No modo local o pacote é o de public.sap_local, já lido no
        # loadDockWidget (com o banco do login do operador): o painel se refaz
        # com ele, e é o painel do modo local.
        if self.sapActivity is None:
            return
        self.sapActivity = self.sap.getActivity(self.sapActivity.getData())
        self.loadShortcuts()
        self.productionTools = self.guiFactory.makeLocalProductionToolsDock(self, self.productionTools)
        self.qgis.addDockWidget(self.productionTools, side='left')

    def loadDockWidget(self, dbusername, dbpassword, dbhost, dbport, dbname):
        pg = Postgresql(dbname, dbusername, dbhost, dbport, dbpassword)
        activityData = self.readLocalPackage(pg)
        reason = self.getUnsupportedReason(activityData)
        if reason:
            self.showErrorMessageBox(self.qgis.getMainWindow(), 'Atividade não atendida', reason)
            return None
        # O SAP Gerente grava o pacote sem segredo (sem `user`, `password` e a
        # senha de `local_db`): o banco local vem do login do operador.
        activityData.setdefault('local_db', {})
        activityData['local_db']['password'] = dbpassword
        activityData['local_db']['username'] = dbusername
        activityData['local_db']['host'] = dbhost
        activityData['local_db']['port'] = dbport
        activityData['local_db']['database'] = dbname
        self.sapActivity = self.sap.getActivity(activityData)
        self.loadShortcuts()
        #self.loadChangeStyleTool( self.sapActivity.getStylesName() )
        self.productionTools = self.guiFactory.makeLocalProductionToolsDock(self)
        self.qgis.addDockWidget(self.productionTools, side='left')
        #self.prodToolsSettings.checkPluginUpdates()
        return self.productionTools

    def showEndActivityDialog(self):
        if self.qgis.hasModifiedLayers():
            self.showInfoMessageBox(
                self.productionTools,
                'Aviso',
                'Salve todas suas alterações antes de finalizar!'
            )
            return

        stepTypeId = self.sapActivity.getStepTypeId()
        noteLayers = self.sapActivity.getNoteLayers()
        try:
            checkStep = self.qgis.checkModifiedLayersByStepId(
                stepTypeId,
                noteLayers
            )
        except Exception as e:
            self.showErrorMessageBox( self.productionTools, 'Erro', str(e) )
            return
        if stepTypeId == 3 and not checkStep:
            self.showInfoMessageBox(
                self.productionTools,
                'Aviso',
                'Existem apontamentos não resolvidos!'
            )
            return
        withoutCorrection = stepTypeId == 2 and checkStep
        result = self.sap.showEndActivityDialog(withoutCorrection)
        if not result:
            return
        #self.resetProject()

    def setScaleVariables(self):
        # Como no remoto: sem escala (denominador_escala null no SAP 3.0), as
        # variáveis de projeto não são definidas.
        scaleDenominator = self.sapActivity.getScaleDenominator()
        if scaleDenominator is None:
            return
        self.qgis.setProjectVariable('escala', scaleDenominator, encrypt=False)
        self.qgis.setProjectVariable('productiontools_scale', scaleDenominator, encrypt=False)

    def loadActivityLayers(self):
        self._loadAndConfigureLayers(self.getActivityLayerNames())

    def loadActivityLayersByNames(self, names):
        # Botão "Carregar camadas" do quadro Dados (widgets/activityData.py).
        if len(names) == 0:
            self.showInfoMessageBox(None, 'Aviso', 'Sem camadas a serem carregadas!')
            return
        layerNames = [ l for l in self.getActivityLayerNames() if l in names]
        self._loadAndConfigureLayers(layerNames)

    def getFieldFileSettingsKey(self):
        return 'productiontools:campo:{0}'.format(self.sapActivity.getVersioning()['repo_id'])

    def getFieldFile(self):
        # O pacote local mora no banco (public.sap_local) e traz só o nome do
        # GeoPackage de campo: vale a pasta usada da última vez nesta
        # atividade, depois a pasta do projeto, e por fim a que o operador
        # escolher (lembrada para as próximas vezes).
        name = campo.nomeDoArquivo(self.sapActivity.getVersioning())
        folders = [self.qgis.getSettingsVariable(self.getFieldFileSettingsKey()), core.QgsProject.instance().homePath()]
        path = campo.localizarArquivo(name, folders)
        if path is not None:
            return path
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.qgis.getMainWindow(),
            'Selecione o GeoPackage de campo da atividade ({0})'.format(name),
            next((folder for folder in folders if folder), ''),
            'GeoPackage de campo ({0})'.format(name)
        )
        if not path:
            return None
        if os.path.basename(path) != name:
            raise campo.CampoError(
                'O arquivo escolhido ({0}) não é o GeoPackage de campo do pacote ({1}).'.format(os.path.basename(path), name)
            )
        return path

    def _loadFieldLayers(self, layerNames):
        versioning = self.sapActivity.getVersioning()
        try:
            path = self.getFieldFile()
            if path is None:
                self.showInfoMessageBox(None, 'Aviso', 'Sem o GeoPackage de campo, as camadas da atividade não foram carregadas.')
                return None
            checked = campo.conferirArquivo(path, versioning)
        except campo.CampoError as e:
            self.showErrorMessageBox(None, 'Aviso', str(e))
            return None
        self.qgis.setSettingsVariable(self.getFieldFileSettingsKey(), os.path.dirname(path))
        self.fieldFile = path
        layers = [ l for l in self.sapActivity.getLayers() if l['nome'] in layerNames ]
        loadedLayerIds, missing = campo.abrirCamadas(path, versioning, layers, checked['repositorio'])
        loadedLayers = core.QgsProject.instance().mapLayers()
        gaps = []
        for layerData in layers:
            layer = next(
                (loadedLayers[i] for i in loadedLayerIds if camadas.tabelaDaCamada(loadedLayers[i]) == (layerData['schema'], layerData['nome'])),
                None
            )
            if layer is None or not layerData.get('filter'):
                continue
            if not camadas.aplicarFiltro(layer, layerData['filter']):
                gaps.append(layerData['nome'])
        self.qgis.groupLayers(loadedLayerIds, self.sapActivity.getLayersGroupName())
        self.fieldGaps = {'missing': missing, 'unfiltered': gaps, 'estado': checked['estado']}
        if missing:
            self.showErrorMessageBox(
                None,
                'Aviso',
                'Camadas não carregadas do GeoPackage de campo: {0}'.format(
                    '; '.join('{0} ({1})'.format(name, reason) for name, reason in missing)
                )
            )
        return loadedLayerIds

    def _loadAndConfigureLayers(self, layerNames):
        # Só a base versionada (4.4.0): o pacote local de outro tipo já é
        # recusado no login, e aqui de novo, sem carregar nada.
        reason = self.sapActivity.getUnsupportedReason()
        if reason:
            self.showErrorMessageBox(None, 'Atividade não atendida', reason)
            return
        self.setScaleVariables()
        loadedLayerIds = self._loadFieldLayers(layerNames)
        if loadedLayerIds is None:
            return

        defaultStyle = self.getActivityStyles()[0] if self.getActivityStyles() else None
        if defaultStyle:
            self.qgis.loadMapLayerStyles(
                loadedLayerIds,
                self.sapActivity.getLayerStyles(),
                defaultStyle
            )
            #self.changeStyleWidget.loadStyles(self.getActivityStyles(), defaultStyle)

        """ matchAndApplyQmlStylesToLayers = self.processingFactoryDsgTools.createProcessing('MatchAndApplyQmlStylesToLayers', self)
        matchAndApplyQmlStylesToLayers.run({
            'layersQml': self.sapActivity.getLayersQml(styleName),
            'layerIds': loadedLayerIds
        }) """

        # No campo os domínios vêm do modelo gravado no GeoPackage do clone:
        # campo.abrirCamadas já põe o editor ValueMap dos rótulos.

        assignMeasureColumnToLayers = self.processingFactoryDsgTools.createProcessing('AssignMeasureColumnToLayers', self)
        assignMeasureColumnToLayers.run({'layerIds': loadedLayerIds})

        alias = self.sapActivity.getLayerALiases()
        # Os algoritmos de apelidos e ações do DsgTools acham a camada pela
        # tabela do endereço, que a camada ogr do arquivo não tem: a mesma
        # semântica, com a camada achada por tabelaDaCamada.
        campo.aplicarApelidos(self.qgis.getLayerFromIds(loadedLayerIds), alias)
        campo.aplicarAcoes(self.qgis.getLayerFromIds(loadedLayerIds), self.sapActivity.getLayerActions())
        rules = self.sapActivity.getRules()
        if rules:
            # O algoritmo do DsgTools descarta provedor diferente de postgres.
            aplicarRegrasDeFormatacao(self.qgis.getLayerFromIds(loadedLayerIds), rules[0]['regra'])

        """ assignConditionalStyleToLayers = self.processingFactoryDsgTools.createProcessing('AssignConditionalStyleToLayers', self)
        assignConditionalStyleToLayers.run({
            'conditionals': self.sapActivity.getLayerConditionalStyle(),
            'layerIds': loadedLayerIds
        }) """

        # setRemoveDuplicateNodePropertyOnLayers = self.processingFactoryDsgTools.createProcessing('SetRemoveDuplicateNodePropertyOnLayers', self)
        # setRemoveDuplicateNodePropertyOnLayers.run({'layerIds': loadedLayerIds})

        frameQuery = self.sapActivity.getFrameQuery()
        if not self.frameLoaded( frameQuery ):
            self.qgis.loadInputData({
                'query': self.sapActivity.getFrameQuery(),
                'epsg': self.sapActivity.getEPSG(),
                'nome': 'moldura',
                'tipo_insumo_id': 100,
                'qml': self.sapActivity.getFrameQml()
            })

        self.qgis.loadLayerActions(loadedLayerIds)

        self.qgis.setPrimaryKeyReadOnly( loadedLayerIds, True )
        self.qgis.setHiddenColumns( loadedLayerIds, self.sapActivity.getHiddenColumns() )

        if self.sapActivity.getStepTypeId() == 3:
            mapLayerIdNote = {}
            noteLayers = self.sapActivity.getNoteLayers()
            for layerNote in noteLayers:
                layerId = next(filter(lambda layerId: layerNote['nome'] in layerId, loadedLayerIds) , None)
                mapLayerIdNote[layerId] = layerNote
            noteLayerIds = mapLayerIdNote.keys()
            loadedNotelayers = self.qgis.getLayerFromIds(noteLayerIds)
            for layer in loadedNotelayers:
                note = mapLayerIdNote[layer.id()]
                self.qgis.setFieldsReadOnly(
                    [layer.id()],
                    [
                        n
                        for n in layer.fields().names()
                        if not(n == note['atributo_justificativa_apontamento'] or n == note['atributo_situacao_correcao'])
                    ],
                    True
                )

        if self.sapActivity.getStepTypeId() == 2:
            self.qgis.loadDefaultFieldValue(
                loadedLayerIds,
                [
                    {
                        'name': 'subfase_id',
                        'value': self.sapActivity.getSubphaseId()
                    }
                ]
            )
            self.qgis.setFieldsReadOnly( loadedLayerIds, ['subfase_id'], True )

        self.prodToolsSettings.initSaveTimer()

        self.validateUserOperations.setWorkspaceWkt( self.sapActivity.getFrameWkt() )
        self.validateUserOperations.setTraceableLayerIds( loadedLayerIds )
        self.validateUserOperations.start()
        self.canvasMonitoring.start()
        self.startMicrocontrole(loadedLayerIds)

        self.loadReviewTool()

        # O LoadThemes do DsgTools casa por uri().schema()/table().
        for theme in self.sapActivity.getThemes():
            self.qgis.loadThemes(theme['definicao_tema'])
        self.sortLayersOnMolduraGroup()

    def getDSGToolsQAWorkflows(self):
        # O quadro Dados do painel pergunta pelos workflows também no modo local.
        return self.sapActivity.getWorkflows()

    def loadDsgToolsworkflowToolbox(self):
        if getattr(self, 'workflowToolbox', None) is not None:
            return
        self.workflowToolbox = self.toolFactoryDsgTools.getTool('WorkflowToolBox', self)
        self.workflowToolbox.run(self.getDSGToolsQAWorkflows())

    def getSapMenus(self):
        menus = self.sapActivity.getMenus()
        # O menu de aquisição do DsgTools acha a camada ogr pela tabela do
        # arquivo (f_<hash> no GeoPackage de campo), não pelo nome da camada.
        return campo.traduzirMenus(menus, self.qgis.getLoadedVectorLayers())

    def runRuleStatistics(self, routineData):
        # O dsgtools:rulestatistics acha a camada pela tabela do endereço.
        result = estatisticaDeRegras(
            routineData['ruleStatistics'],
            [ l for l in self.qgis.getLoadedVectorLayers() if camadas.ehDeCampo(l) ]
        )
        self.htmlMessageDlg = self.messageFactory.createMessage('RuleMessageDialog')
        self.htmlMessageDlg.show(
            self.qgis.getMainWindow(),
            'Aviso',
            result,
            self.qgis
        )
        return result

    def sortLayersOnMolduraGroup(self):
        utils.iface.mapCanvas().freeze(True)
        rootNode = core.QgsProject.instance().layerTreeRoot()
        oldGroup = rootNode.findGroup('MOLDURA_E_INSUMOS')
        newGroup = rootNode.addGroup('MOLDURA_E_INSUMOS')
        auxDict = OrderedDict(
            {
                core.QgsWkbTypes.GeometryType.PointGeometry: [],
                core.QgsWkbTypes.GeometryType.LineGeometry: [],
                core.QgsWkbTypes.GeometryType.PolygonGeometry: [],
            }
        )
        rasterList = []
        for layerTreeView in oldGroup.children():
            lyr = layerTreeView.layer()
            if isinstance(lyr, core.QgsRasterLayer):
                rasterList.append(layerTreeView)
                continue
            if lyr.name() in ("aux_grid_revisao_a", "moldura"):
                idx = 0 if lyr.name() == "aux_grid_revisao_a" else -1
                myClone = layerTreeView.clone()
                newGroup.insertChildNode(idx, myClone)
                oldGroup.removeChildNode(layerTreeView)
                continue
            auxDict[lyr.geometryType()].append(layerTreeView)
        for geomType, layerTreeViewList in auxDict.items():
            for layerTreeView in sorted(layerTreeViewList, key=lambda x: x.layer().name(), reverse=False):
                myClone = layerTreeView.clone()
                newGroup.insertChildNode(-1, myClone)
                oldGroup.removeChildNode(layerTreeView)
        for rasterNode in sorted(rasterList, key=lambda x: x.layer().name().lower(), reverse=False):
            myClone = rasterNode.clone()
            newGroup.insertChildNode(-1, myClone)
            oldGroup.removeChildNode(rasterNode)
        rootNode.removeChildNode(oldGroup)
        utils.iface.mapCanvas().freeze(False)

    def readProjectCallback(self):
        self.prodToolsSettings.initSaveTimer()
        self.canvasMonitoring.start()

    def createProjectCallback(self):
        self.canvasMonitoring.stop()
        self.stopMicrocontrole()

    def loadReviewTool(self):
        frameQuery = self.sapActivity.getFrameQuery()
        if not self.frameLoaded(frameQuery):
            self.qgis.loadInputData({
                'query': self.sapActivity.getFrameQuery(),
                'epsg': self.sapActivity.getEPSG(),
                'nome': 'moldura',
                'tipo_insumo_id': 100,
                'qml': self.sapActivity.getFrameQml()
            })
        gridLayer = self._loadFieldReviewGrid()
        if gridLayer is None:
            return

        # Check for field existence and build appropriate filter
        fields = [field.name() for field in gridLayer.fields()]
        has_new_fields = 'unidade_trabalho_id' in fields and 'etapa_id' in fields

        if has_new_fields:
            filter_expr = f'unidade_trabalho_id = {self.sapActivity.getWorkUnitId()} AND etapa_id = {self.sapActivity.getStepId()}'
        else:
            # Fall back to old atividade_id filter
            filter_expr = f'atividade_id = {self.sapActivity.getId()}'

        camadas.aplicarFiltro(gridLayer, filter_expr)

        self.moveLayerToGroup(gridLayer.id())

        reviewToolBar = self.toolFactoryDsgTools.getTool('ReviewToolBar', self)
        if gridLayer.featureCount() != 0:
            reviewToolBar.run(gridLayer)
            return

        createReviewGrid = self.processingFactoryDsgTools.createProcessing('CreateReviewGrid', self)
        scaleDenominator = self.sapActivity.getScaleDenominator()
        frameLyr = core.QgsProject.instance().mapLayersByName('moldura')[0]

        # Determine grid size based on scale. Sem escala (denominador_escala null
        # no SAP 3.0), vale a grade das escalas menores que 1:10.000, como no remoto.
        if scaleDenominator is not None and scaleDenominator <= 10000:
            param = {
                'input': frameLyr,
                'x_grid_size': (0.001) if frameLyr.crs().isGeographic() else (1e2),
                'y_grid_size': (0.001) if frameLyr.crs().isGeographic() else (1e2)
            }
        else:
            param = {
                'input': frameLyr,
                'x_grid_size': (0.01) if frameLyr.crs().isGeographic() else (1e3),
                'y_grid_size': (0.008) if frameLyr.crs().isGeographic() else (800)
            }

        # O lançador do CreateReviewGrid pede os três identificadores, como no remoto.
        param.update({
            'related_task_id': self.sapActivity.getId(),
            'unit_work_id': self.sapActivity.getWorkUnitId(),
            'step_id': self.sapActivity.getStepId()
        })

        result = createReviewGrid.run(param)
        outputLayer = result['OUTPUT']
        reviewToolBar.run(gridLayer, outputLayer=outputLayer)

    def _loadFieldReviewGrid(self):
        # A grade de revisão do campo é a classe aux_grid_revisao_a do
        # GeoPackage, quando o clone a tem. A grade nova gravada no arquivo
        # recebe a identidade de cada célula antes de gravar (campo.GuardaDeCampo).
        gridLayer = next(
            (l for l in self.qgis.getLoadedVectorLayers() if camadas.ehDeCampo(l) and camadas.tabelaDaCamada(l)[1] == 'aux_grid_revisao_a'),
            None
        )
        if gridLayer is not None:
            return gridLayer
        versioning = self.sapActivity.getVersioning()
        gridData = next((d for d in versioning.get('datasets') or [] if d.get('nome') == 'aux_grid_revisao_a'), None)
        if gridData is None or not getattr(self, 'fieldFile', None):
            core.QgsMessageLog.logMessage(
                'Lacuna: o GeoPackage de campo não tem aux_grid_revisao_a; a ferramenta de revisão não foi carregada.',
                camadas.LOG_TAG, core.Qgis.MessageLevel.Warning
            )
            return None
        loadedLayerIds, _ = campo.abrirCamadas(
            self.fieldFile, versioning, [{'schema': gridData.get('schema'), 'nome': 'aux_grid_revisao_a'}]
        )
        if not loadedLayerIds:
            return None
        return core.QgsProject.instance().mapLayer(loadedLayerIds[0])

    def moveLayerToGroup(self, loadedLayerId, positionToInsert=0):
        utils.iface.mapCanvas().freeze(True)
        rootNode = core.QgsProject.instance().layerTreeRoot()
        group = rootNode.findGroup('MOLDURA_E_INSUMOS')
        lyrNode = rootNode.findLayer(loadedLayerId)
        myClone = lyrNode.clone()
        group.insertChildNode(positionToInsert, myClone)
        rootNode.removeChildNode(lyrNode)
        utils.iface.mapCanvas().freeze(False)

    def saveControllerInfo(self, user, userID, startTime, endTime):
        # O quadro "Controle" grava no banco LOCAL do login (public.sap_local),
        # não num banco de produção.
        pg = Postgresql(
            self.sapActivity.getDatabaseName(),
            self.sapActivity.getDatabaseUserName() ,
            self.sapActivity.getDatabaseServer(),
            self.sapActivity.getDatabasePort(),
            self.sapActivity.getDatabasePassword()
        )
        pg.execute(
            '''
                UPDATE public.sap_local
                SET
                    nome_usuario = %s,
                    usuario_uuid = %s,
                    data_inicio = %s,
                    data_fim = %s
                RETURNING *;
            ''',
            (
                user, userID, startTime, endTime
            )
        )

    def getControllerInfo(self):
        pg = Postgresql(
            self.sapActivity.getDatabaseName(),
            self.sapActivity.getDatabaseUserName() ,
            self.sapActivity.getDatabaseServer(),
            self.sapActivity.getDatabasePort(),
            self.sapActivity.getDatabasePassword()
        )
        result = pg.execute(
            '''
                SELECT
                    EXTRACT (EPOCH FROM data_inicio),
                    EXTRACT (EPOCH FROM data_fim),
                    nome_usuario,
                    usuario_uuid
                FROM public.sap_local;
            ''',
            ()
        )
        return result[0]

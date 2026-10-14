from collections import OrderedDict
from qgis.PyQt.QtWidgets import QMessageBox
from SAP_Operador.controllers.prodToolsCtrl import ProdToolsCtrl
from qgis import core, gui, utils

import os
import json
from qgis.PyQt import sip

from SAP_Operador.modules.versionamento import camadas
from SAP_Operador.modules.versionamento.regras import aplicarRegrasDeFormatacao


class RemoteProdToolsDockCtrl(ProdToolsCtrl):

    def __init__(
            self,
            sap,
            qgis,
            databaseFactory,
            processingFactoryDsgTools,
            fme,
            prodToolsSettings,
            toolFactoryDsgTools,
            pomodoro=None,
            guiFactory=None,
            spatialVerificationFactory=None,
            canvasMonitoring=None,
        ):
        super(RemoteProdToolsDockCtrl, self).__init__(
            sap=sap,
            qgis=qgis,
            databaseFactory=databaseFactory,
            processingFactoryDsgTools=processingFactoryDsgTools,
            fme=fme,
            prodToolsSettings=prodToolsSettings,
            toolFactoryDsgTools=toolFactoryDsgTools,
            pomodoro=pomodoro,
            guiFactory=guiFactory,
            spatialVerificationFactory=spatialVerificationFactory,
            canvasMonitoring=canvasMonitoring,
        )
        self.workflowToolbox = None

        # Inicializa com o total de violação de regras em 1.
        self.total_rule_violations = 1

    def authUser(self, username, password, server):
        self.sap.setServer(server)
        #self.prodToolsSettings.checkPluginUpdates()
        self.qgis.setProjectVariable('productiontools:user', username)
        self.qgis.setProjectVariable('productiontools:password', password)
        self.qgis.setSettingsVariable('productiontools:server', server)
        return self.sap.authUser(username, password, server)

    def checkPluginUpdates(self, server):
        self.sap.setServer(server)
        return self.prodToolsSettings.checkPluginUpdates()

    def reload(self):
        try:
            self.prodToolsSettings.checkPluginUpdates()
            if self.productionTools is None:
                return
            self.removeDock()
            self.sapActivity = self.sap.getActivity()
            if self.sapActivity is None:
                return
            self.loadShortcuts()
            self.productionTools = self.guiFactory.makeRemoteProductionToolsDock(self, self.sap, self.productionTools)
            if self.workflowToolbox is None:
                self.loadDsgToolsworkflowToolbox()
            self.workflowToolbox.refreshToolboxObject()
            self.qgis.addDockWidget(self.productionTools, side='left')
        except Exception as e:
            error_message = str(e)
            if "Sem atividades disponíveis para iniciar" in error_message:
                QMessageBox.information(
                    self.qgis.getMainWindow(),
                    "Informação",
                    "Não há atividades disponíveis para iniciar no momento.",
                    QMessageBox.StandardButton.Ok
                )
                self.cleanupAfterNoActivities()
                self.closeOperatorWindow()
            else:
                QMessageBox.warning(
                    self.qgis.getMainWindow(),
                    "Erro",
                    f"Ocorreu um erro inesperado: {error_message}",
                    QMessageBox.StandardButton.Ok
                )
            return False
        return True

    def cleanupAfterNoActivities(self):
        if hasattr(self, 'validateUserOperations') and self.validateUserOperations:
            self.validateUserOperations.stop()
        if hasattr(self, 'canvasMonitoring') and self.canvasMonitoring:
            self.canvasMonitoring.stop()
        self.stopMicrocontrole()
        if hasattr(self, 'changeStyleWidget') and self.changeStyleWidget and not sip.isdeleted(self.changeStyleWidget):
            self.changeStyleWidget.setEnabled(False)

    def closeOperatorWindow(self):
        if hasattr(self, 'productionTools') and self.productionTools:
            self.removeDock()
        if self.qgis:
            self.qgis.cleanProject()

    def loadDockWidget(self, sapActivity=None):
        self.sapActivity = self.sap.getActivity() if sapActivity is None else sapActivity
        if not self.sapActivity:
            return
        self.loadShortcuts()
        self.loadChangeStyleTool( self.sapActivity.getStylesName() )
        self.productionTools = self.guiFactory.makeRemoteProductionToolsDock(self, self.sap)
        self.qgis.addDockWidget(self.productionTools, side='left')
        #self.prodToolsSettings.checkPluginUpdates()

        genericSelectionToolParameters = self.processingFactoryDsgTools.createProcessing('GenericSelectionToolParameters', self)
        genericSelectionToolParameters.run({})

        return self.productionTools

    def loadDockWidgetExternally(self, sapActivity, sap):
        self.sapActivity = sapActivity
        self.loadShortcuts()
        self.loadChangeStyleTool( self.sapActivity.getStylesName() )
        self.productionTools = self.guiFactory.makeRemoteProductionToolsDock(self, sap)
        self.qgis.addDockWidget(self.productionTools, side='left')
        #self.prodToolsSettings.checkPluginUpdates()

        genericSelectionToolParameters = self.processingFactoryDsgTools.createProcessing('GenericSelectionToolParameters', self)
        genericSelectionToolParameters.run({})

        return self.productionTools

    def showEndActivityDialog(self):
        if self.isVersionedActivity():
            failed = self.saveVersionedLayers()
            if failed:
                self.showErrorMessageBox(
                    self.productionTools,
                    'Aviso',
                    'Salvamento recusado antes de finalizar: {0}'.format('<br>'.join(failed))
                )
                return
        if self.qgis.hasModifiedLayers():
            self.showInfoMessageBox(
                self.productionTools,
                'Aviso',
                'Salve todas suas alterações antes de finalizar!'
            )
            return
        # Adicção da verificação de etapa, se for revisão, não cobra Workflow
        if self.sapActivity.getStepTypeId() != 2 and len(self.getDSGToolsQAWorkflows()) > 0 and (self.workflowToolbox is None or not self.workflowToolbox.allWorkflowsAreFinishedWithoutFlags()):
            self.showInfoMessageBox(
                self.productionTools,
                'Aviso',
                'Rode todos os processos de validação do DSGTools e corrija as flags antes de finalizar!'
            )
            return
        # Verifica se a rotina de Estatística de Regras possui erros e (02SET25) confere se não é a etapa de revisão:
        if (hasattr(self, 'total_rule_violations') and self.total_rule_violations > 0) and self.sapActivity.getStepTypeId() != 2:
            self.showInfoMessageBox(
                self.productionTools,
                'Aviso',
                'A atividade somente pode ser finalizada quando a rotina de Estatística de Regras não possuir erros.'
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
        result = self.sap.showEndActivityDialog(withoutCorrection, stepTypeId)
        if not result:
            return
        self.resetProject()

    def setScaleVariables(self):
        # O SAP 3.0 manda denominador_escala null quando as folhas da unidade de
        # trabalho têm escalas diferentes ou nenhuma: sem ela, as variáveis de
        # projeto não são definidas, em vez de o carregamento falhar no int('-').
        scaleDenominator = self.sapActivity.getScaleDenominator()
        if scaleDenominator is None:
            return
        self.qgis.setProjectVariable('escala', scaleDenominator, encrypt=False)
        self.qgis.setProjectVariable('productiontools_scale', scaleDenominator, encrypt=False)

    def loadActivityLayers(self):
        self._loadAndConfigureLayers(self.getActivityLayerNames())

    def loadActivityLayersByNames(self, names):
        if len(names) == 0:
            self.showInfoMessageBox(None, 'Aviso', 'Sem camadas a serem carregadas!')
            return
        layerNames = [ l for l in self.getActivityLayerNames() if l in names]
        self._loadAndConfigureLayers(layerNames)

    def isVersionedActivity(self):
        return bool(self.sapActivity) and self.sapActivity.isVersioned()

    def getVersioningServiceBase(self):
        # Registra (ou renova) a conexão do provedor com o repasse do SAP, com o
        # token do SAP lido a cada pedido e o novo login num 401.
        sapApi = self.sap.sapApi
        camadas.conectar(sapApi.getServer(), sapApi.getToken, sapApi._reAuth)
        return camadas.base(self.sapActivity.getVersioning(), sapApi.getServer())

    def _loadVersionedLayers(self, layerNames):
        # Tipo 4: as classes abrem pelo provedor dsgversioning, do clone que o
        # SAP criou para a atividade (já recortado pela unidade de trabalho).
        serviceBase = self.getVersioningServiceBase()
        layers = [ l for l in self.sapActivity.getLayers() if l['nome'] in layerNames ]
        loadedLayerIds, missing = camadas.abrirCamadas(serviceBase, self.sapActivity.getVersioning(), layers)
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
        self.versioningGaps = {'missing': missing, 'unfiltered': gaps}
        if missing:
            self.showErrorMessageBox(
                None,
                'Aviso',
                'Camadas não carregadas pelo versionamento: {0}'.format(
                    '; '.join('{0} ({1})'.format(name, reason) for name, reason in missing)
                )
            )
        return loadedLayerIds

    def _loadPostgisLayers(self, layerNames):
        loadLayersFromPostgis = self.processingFactoryDsgTools.createProcessing('LoadLayersFromPostgis', self)
        result = loadLayersFromPostgis.run({
            'dbName' : self.sapActivity.getDatabaseName(),
            'dbHost' : self.sapActivity.getDatabaseServer(),
            'layerNames' : layerNames,
            'dbPassword' : self.sapActivity.getDatabasePassword(),
            'dbPort' : self.sapActivity.getDatabasePort(),
            'dbUser' : self.sapActivity.getDatabaseUserName()
        })
        loadedLayerIds = result['OUTPUT']

        assingFilterToLayers = self.processingFactoryDsgTools.createProcessing('AssingFilterToLayers', self)
        assingFilterToLayers.run({'layers': self.sapActivity.getLayers()})

        groupLayers = self.processingFactoryDsgTools.createProcessing('GroupLayers', self)
        groupLayers.run({'layerIds': loadedLayerIds})
        return loadedLayerIds

    def _loadAndConfigureLayers(self, layerNames):
        self.setScaleVariables()
        versioned = self.isVersionedActivity()
        if versioned:
            loadedLayerIds = self._loadVersionedLayers(layerNames)
        else:
            loadedLayerIds = self._loadPostgisLayers(layerNames)

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

        if not versioned:
            assignValueMapToLayers = self.processingFactoryDsgTools.createProcessing('AssignValueMapToLayers', self)
            database = self.getActivityDatabase()
            assignValueMapToLayers.run({
                'valueMaps': {
                        layer["nome"]: database.getAttributeValueMap(layer["nome"], layer["schema"])
                        for layer in self.sapActivity.getLayers()
                },
                'layerIds': loadedLayerIds
            })
        # No versionado os domínios vêm do modelo do repositório: o provedor já
        # entrega cada campo de domínio com o editor ValueMap dos rótulos.

        assignMeasureColumnToLayers = self.processingFactoryDsgTools.createProcessing('AssignMeasureColumnToLayers', self)
        assignMeasureColumnToLayers.run({'layerIds': loadedLayerIds})

        alias = self.sapActivity.getLayerALiases()
        if alias:
            assignAliasesToLayers = self.processingFactoryDsgTools.createProcessing('AssignAliasesToLayers', self)
            assignAliasesToLayers.run({
                'aliases': alias,
                'layerIds': loadedLayerIds
            })

        assignActionsToLayers = self.processingFactoryDsgTools.createProcessing('AssignActionsToLayers', self)
        assignActionsToLayers.run({
            'actions': self.sapActivity.getLayerActions(),
            'layerIds': loadedLayerIds
        })
        rules = self.sapActivity.getRules()
        if rules and versioned:
            # O algoritmo do DsgTools descarta provedor diferente de postgres: as
            # regras de formatação da camada versionada se aplicam aqui, com a
            # mesma semântica.
            aplicarRegrasDeFormatacao(self.qgis.getLayerFromIds(loadedLayerIds), rules[0]['regra'])
        elif rules:
            assignFormatRulesToLayers = self.processingFactoryDsgTools.createProcessing('AssignFormatRulesToLayers', self)
            assignFormatRulesToLayers.run({
                'rules': rules,
                'layerIds': loadedLayerIds
            })
        else:
            # Caso não seja carregada nenhuma regra, o total de violações de regras é tornado 0.
            self.total_rule_violations = 0

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

        loadThemes = self.processingFactoryDsgTools.createProcessing('LoadThemes', self)
        for theme in self.sapActivity.getThemes():
            loadThemes.run({'themes': theme['definicao_tema']})
        self.sortLayersOnMolduraGroup()

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
            if lyr.name() in ("moldura"):
                idx = -1
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

    def runRuleStatistics(self, routineData):
        result = super().runRuleStatistics(routineData)
        # Calcula quantas violações de regras tem e armazena em self.total_rule_violations
        self.total_rule_violations = sum(
            len(v) for k, v in result.items()
            if 'atributo incorreto' in k.lower() or 'preencher atributo' in k.lower()
        )
        return result

    def reconnectVersionedLayers(self):
        # Projeto reaberto: as camadas do provedor abrem antes do login e ficam
        # inválidas (o token não vai para o projeto). Com o login refeito, a
        # conexão se registra e cada camada inválida reabre pela mesma fonte.
        activity = self.sap.getActivityDataModel()
        if not (activity and activity.getData() and activity.isVersioned()):
            return []
        sapApi = self.sap.sapApi
        camadas.conectar(sapApi.getServer(), sapApi.getToken, sapApi._reAuth)
        reopened = []
        for layer in self.qgis.getLoadedVectorLayers():
            if camadas.ehVersionada(layer) and not layer.isValid():
                layer.setDataSource(layer.source(), layer.name(), layer.providerType())
                reopened.append(layer.id())
        return reopened

    def readProjectCallback(self):
        if self.productionTools:
            self.productionTools.close()

        user = self.qgis.getProjectVariable('productiontools:user')
        password = self.qgis.getProjectVariable('productiontools:password')
        server = self.qgis.getSettingsVariable('productiontools:server')
        if not(user and password and server):
            return

        self.sap.setServer(server)
        if self.prodToolsSettings.checkPluginUpdates():
            return
        self.sap.authUser(user, password, server)


        if self.sap.isValidActivity():
            self.reconnectVersionedLayers()
            self.prodToolsSettings.initSaveTimer()
            self.canvasMonitoring.start()
            return
        self.qgis.cleanProject()
        self.showInfoMessageBox(
            self.qgis.getMainWindow(),
            'Aviso',
            '''
            <p style="color:red">
                Esse projeto não pode ser acessado. Carregue um novo projeto.
            </p>
            '''
        )

    def createProjectCallback(self):
        if self.productionTools:
            self.productionTools.close()
        self.canvasMonitoring.stop()
        self.stopMicrocontrole()

    def getDSGToolsQAWorkflows(self):
        return self.sapActivity.getWorkflows()

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
        if self.isVersionedActivity():
            self._loadVersionedReviewTool()
            return
        candidateLayerList = core.QgsProject.instance().mapLayersByName('aux_grid_revisao_a')
        if not candidateLayerList:
            loadLayersFromPostgis = self.processingFactoryDsgTools.createProcessing('LoadLayersFromPostgis', self)
            result = loadLayersFromPostgis.run({
                'dbName': self.sapActivity.getDatabaseName(),
                'dbHost': self.sapActivity.getDatabaseServer(),
                'layerNames': ['aux_grid_revisao_a'],
                'dbPassword': self.sapActivity.getDatabasePassword(),
                'dbPort': self.sapActivity.getDatabasePort(),
                'dbUser': self.sapActivity.getDatabaseUserName()
            })
            loadedLayerIds = result['OUTPUT']
            if not loadedLayerIds:
                return
            gridLayer = core.QgsProject.instance().mapLayer(loadedLayerIds[0])
        else:
            gridLayer = candidateLayerList[0]
        self.moveLayerToGroup(gridLayer)

        # Check for field existence and build appropriate filter
        fields = [field.name() for field in gridLayer.fields()]
        has_new_fields = 'unidade_trabalho_id' in fields and 'etapa_id' in fields

        if has_new_fields:
            filter_expr = f'unidade_trabalho_id = {self.sapActivity.getWorkUnitId()} AND etapa_id = {self.sapActivity.getStepId()}'
        else:
            # Fall back to old atividade_id filter
            filter_expr = f'atividade_id = {self.sapActivity.getId()}'

        assingFilterToLayers = self.processingFactoryDsgTools.createProcessing('AssingFilterToLayers', self)
        assingFilterToLayers.run({
            'layers': [
                {
                    'filter': filter_expr,
                    'nome': 'aux_grid_revisao_a',
                    'schema': camadas.tabelaDaCamada(gridLayer)[0]
                }
            ]
        })

        reviewToolBar = self.toolFactoryDsgTools.getTool('ReviewToolBar', self)
        if gridLayer.featureCount() != 0:
            reviewToolBar.run(gridLayer)
            return
        reviewToolBar.run(gridLayer, outputLayer=self._createReviewGrid())

    def _createReviewGrid(self):
        # A grade nova sobre a moldura da unidade de trabalho; quem a grava na
        # camada é o ReviewToolBar (no versionado, pelo provedor).
        createReviewGrid = self.processingFactoryDsgTools.createProcessing('CreateReviewGrid', self)
        scaleDenominator = self.sapActivity.getScaleDenominator()
        frameLyr = core.QgsProject.instance().mapLayersByName('moldura')[0]

        # Determine grid size based on scale. Sem escala (denominador_escala null
        # no SAP 3.0), vale a grade das escalas menores que 1:10.000.
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

        param.update({
            'related_task_id': self.sapActivity.getId(),
            'unit_work_id': self.sapActivity.getWorkUnitId(),
            'step_id': self.sapActivity.getStepId()
        })

        result = createReviewGrid.run(param)
        return result['OUTPUT']

    def _warnReviewGrid(self, text):
        # Aviso sem caixa modal: a ferramenta de revisão carrega junto com as
        # camadas, também nas atividades que não revisam.
        self.reviewGridGap = text
        core.QgsMessageLog.logMessage(text, camadas.LOG_TAG, core.Qgis.MessageLevel.Warning)
        try:
            utils.iface.messageBar().pushMessage('SAP Operador', text, level=core.Qgis.MessageLevel.Warning, duration=10)
        except Exception:
            pass

    def _loadVersionedReviewTool(self):
        # A grade de revisão do versionado mora na classe aux_grid_revisao_a do
        # repositório da atividade (o clone que o SAP criou, com as camadas da
        # subfase): ela abre pelo provedor, filtrada por unidade de trabalho e
        # etapa, e a grade nova é gravada pelo provedor, pelas rotas do SAP,
        # com a cobrança do modelo e da permissão da etapa. Na finalização ela
        # sobe ao bloco com o resto do clone, como a do banco no tipo 2.
        self.reviewGridGap = None
        gridLayer = next(
            (l for l in self.qgis.getLoadedVectorLayers() if camadas.ehVersionada(l) and camadas.tabelaDaCamada(l)[1] == 'aux_grid_revisao_a'),
            None
        )
        if gridLayer is None:
            versioning = self.sapActivity.getVersioning()
            gridData = next((d for d in versioning.get('datasets') or [] if d.get('nome') == 'aux_grid_revisao_a'), None)
            if gridData is None:
                self._warnReviewGrid(
                    'Ferramenta de revisão não carregada: o repositório desta atividade não tem a classe '
                    'aux_grid_revisao_a, onde a grade de revisão da base versionada é gravada. Para revisar com '
                    'a grade, a camada aux_grid_revisao_a precisa estar entre as camadas da subfase.'
                )
                return
            loadedLayerIds, missing = camadas.abrirCamadas(
                self.getVersioningServiceBase(), versioning, [{'schema': gridData.get('schema'), 'nome': 'aux_grid_revisao_a'}]
            )
            if not loadedLayerIds:
                self._warnReviewGrid(
                    'Ferramenta de revisão não carregada: a grade de revisão não abriu pelo versionamento ({0}).'.format(
                        '; '.join(reason for _, reason in missing) or 'camada inválida'
                    )
                )
                return
            gridLayer = core.QgsProject.instance().mapLayer(loadedLayerIds[0])
            self.qgis.groupLayers(loadedLayerIds, self.sapActivity.getLayersGroupName())
        fields = [field.name() for field in gridLayer.fields()]
        if 'unidade_trabalho_id' in fields and 'etapa_id' in fields:
            filter_expr = f'unidade_trabalho_id = {self.sapActivity.getWorkUnitId()} AND etapa_id = {self.sapActivity.getStepId()}'
        else:
            filter_expr = f'atividade_id = {self.sapActivity.getId()}'
        camadas.aplicarFiltro(gridLayer, filter_expr)
        reviewToolBar = self.toolFactoryDsgTools.getTool('ReviewToolBar', self)
        if gridLayer.featureCount() != 0:
            reviewToolBar.run(gridLayer)
            return
        reviewToolBar.run(gridLayer, outputLayer=self._createReviewGrid())

    def showVersioningPanel(self):
        if not self.isVersionedActivity():
            return
        from SAP_Operador.modules.versionamento.painel import VersioningPanel
        self.versioningPanel = VersioningPanel(
            self.qgis.getMainWindow(),
            utils.iface,
            self.getVersioningServiceBase(),
            self.sapActivity.getVersioning()
        )
        self.versioningPanel.show()
        return self.versioningPanel

    def saveVersionedLayers(self):
        # Finalização do versionado: salva tudo antes de chamar o finaliza. As
        # camadas do provedor gravam no clone pelo serviço; outras camadas
        # modificadas continuam cobradas pelo aviso de sempre.
        failed = []
        for layer in self.qgis.getLoadedVectorLayers():
            if not (camadas.ehVersionada(layer) and layer.isEditable() and layer.isModified()):
                continue
            if not layer.commitChanges(False):
                failed.append('{0}: {1}'.format(layer.name(), ' '.join(layer.commitErrors())))
        return failed

    def loadDsgToolsworkflowToolbox(self):
        if self.workflowToolbox is not None:
            return
        self.workflowToolbox = self.toolFactoryDsgTools.getTool('WorkflowToolBox', self)
        self.workflowToolbox.run(self.getDSGToolsQAWorkflows())

    def moveLayerToGroup(self, layer, positionToInsert=0):
        root = core.QgsProject.instance().layerTreeRoot()
        mylayer = root.findLayer(layer.id())
        myClone = mylayer.clone()
        parent = mylayer.parent()

        group = root.findGroup(self.sapActivity.getLayersGroupName())
        group.insertChildNode(positionToInsert, myClone)

        parent.removeChildNode(mylayer)

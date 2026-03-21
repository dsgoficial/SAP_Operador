from collections import OrderedDict
from qgis.PyQt.QtWidgets import QMessageBox
from SAP_Operador.controllers.prodToolsCtrl import ProdToolsCtrl
from qgis import core, gui, utils

import os
import json
from qgis.PyQt import sip


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
        self.prodToolsSettings.reclassifyMode.connect(self.handleReclassifyMode)

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

    def loadActivityLayers(self):
        scale = self.sapActivity.getScale()
        self.qgis.setProjectVariable('escala', int(scale.split(':')[-1]), encrypt=False)
        self.qgis.setProjectVariable('productiontools_scale', int(scale.split(':')[-1]), encrypt=False)
        loadLayersFromPostgis = self.processingFactoryDsgTools.createProcessing('LoadLayersFromPostgis', self)
        result = loadLayersFromPostgis.run({
            'dbName' : self.sapActivity.getDatabaseName(),
            'dbHost' : self.sapActivity.getDatabaseServer(),
            'layerNames' : self.getActivityLayerNames(),
            'dbPassword' : self.sapActivity.getDatabasePassword(),
            'dbPort' : self.sapActivity.getDatabasePort(),
            'dbUser' : self.sapActivity.getDatabaseUserName()
        })
        loadedLayerIds = result['OUTPUT']

        assingFilterToLayers = self.processingFactoryDsgTools.createProcessing('AssingFilterToLayers', self)
        assingFilterToLayers.run({'layers': self.sapActivity.getLayers()})

        groupLayers = self.processingFactoryDsgTools.createProcessing('GroupLayers', self)
        groupLayers.run({'layerIds': loadedLayerIds})

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

        assignValueMapToLayers = self.processingFactoryDsgTools.createProcessing('AssignValueMapToLayers', self)
        database = self.getActivityDatabase()
        assignValueMapToLayers.run({
            'valueMaps': {
                    layer["nome"]: database.getAttributeValueMap(layer["nome"], layer["schema"])
                    for layer in self.sapActivity.getLayers()
            },
            'layerIds': loadedLayerIds
        })

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
        if rules:
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

        self.loadReviewTool()

        loadThemes = self.processingFactoryDsgTools.createProcessing('LoadThemes', self)
        for theme in self.sapActivity.getThemes():
            loadThemes.run({'themes': theme['definicao_tema']})
        self.sortLayersOnMolduraGroup()

    def loadActivityLayersByNames(self, names):
        if len(names) == 0:
            self.showInfoMessageBox(None, 'Aviso', 'Sem camadas a serem carregadas!')
            return
        layerNames = [ l for l in self.getActivityLayerNames() if l in names]
        scale = self.sapActivity.getScale()
        self.qgis.setProjectVariable('escala', int(scale.split(':')[-1]), encrypt=False)
        self.qgis.setProjectVariable('productiontools_scale', int(scale.split(':')[-1]), encrypt=False)
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

        defaultStyle = self.getActivityStyles()[0] if self.getActivityStyles() else None
        if defaultStyle:
            self.qgis.loadMapLayerStyles(
                loadedLayerIds,
                self.sapActivity.getLayerStyles(),
                defaultStyle
            )
            # self.changeStyleWidget.loadStyles(self.getActivityStyles(), defaultStyle)

        """ matchAndApplyQmlStylesToLayers = self.processingFactoryDsgTools.createProcessing('MatchAndApplyQmlStylesToLayers', self)
        matchAndApplyQmlStylesToLayers.run({
            'layersQml': self.sapActivity.getLayersQml(styleName),
            'layerIds': loadedLayerIds
        }) """

        assignValueMapToLayers = self.processingFactoryDsgTools.createProcessing('AssignValueMapToLayers', self)
        database = self.getActivityDatabase()
        assignValueMapToLayers.run({
            'valueMaps': {
                    layer["nome"]: database.getAttributeValueMap(layer["nome"], layer["schema"])
                    for layer in self.sapActivity.getLayers()
            },
            'layerIds': loadedLayerIds
        })

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
        if rules:
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
        self.total_rule_violations = len(result['[REGRAS] : Atributo incorreto']) + len(result['[REGRAS] : Preencher atributo'])
        return result

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

    def getDSGToolsQAWorkflows(self):
        return self.sapActivity.getWorkflows()

    def handleReclassifyMode(self):
        if not (self.acquisitionMenu and self.acquisitionMenu.menuDock):
            return
        self.acquisitionMenu.menuDock.reclassifyCkb.setChecked( not self.acquisitionMenu.menuDock.reclassifyCkb.isChecked() )

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
                    'schema': gridLayer.dataProvider().uri().schema()
                }
            ]
        })

        reviewToolBar = self.toolFactoryDsgTools.getTool('ReviewToolBar', self)
        if gridLayer.featureCount() != 0:
            reviewToolBar.run(gridLayer)
            return

        # Set up grid creation parameters
        createReviewGrid = self.processingFactoryDsgTools.createProcessing('CreateReviewGrid', self)
        scale = self.sapActivity.getScale()
        frameLyr = core.QgsProject.instance().mapLayersByName('moldura')[0]

        # Determine grid size based on scale
        if int(scale.split(':')[-1]) <= 10000:
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


        outputLayer = result['OUTPUT']
        reviewToolBar.run(gridLayer, outputLayer=outputLayer)

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

        group = root.findGroup(self.sapActivity.getDatabaseName())
        group.insertChildNode(positionToInsert, myClone)

        parent.removeChildNode(mylayer)

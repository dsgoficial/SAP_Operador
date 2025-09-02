from collections import OrderedDict
from SAP_Operador.factories.GUIFactory import GUIFactory
from SAP_Operador.factories.timerFactory import TimerFactory
from SAP_Operador.factories.spatialVerificationFactory import SpatialVerificationFactory
from PyQt5.QtWidgets import QMessageBox
from SAP_Operador.controllers.prodToolsCtrl import ProdToolsCtrl
from PyQt5 import QtWidgets
from qgis import core, gui, utils

import os
import json
import sip

from SAP_Operador.widgets.pomodoro import Pomodoro
from SAP_Operador.monitoring.canvas import Canvas


class RemoteProdToolsDockCtrl(ProdToolsCtrl):

    iconRootPath = os.path.join(
            os.path.dirname(__file__),
            '..',
            'icons'
    )
    
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
        super(RemoteProdToolsDockCtrl, self).__init__()
        self.sap = sap
        self.qgis = qgis
        self.fme = fme
        self.pomodoro = Pomodoro() if pomodoro is None else pomodoro
        self.canvasMonitoring = Canvas() if canvasMonitoring is None else canvasMonitoring
        self.canvasMonitoring.changeStatus.connect(self.pomodoro.setWorkStatusText)
        self.databaseFactory = databaseFactory
        self.processingFactoryDsgTools = processingFactoryDsgTools
        self.guiFactory = GUIFactory() if guiFactory is None else guiFactory
        self.spatialVerificationFactory = SpatialVerificationFactory() if spatialVerificationFactory is None else spatialVerificationFactory
        self.prodToolsSettings = prodToolsSettings
        self.toolFactoryDsgTools = toolFactoryDsgTools
        self.sapActivity = None
        self.productionTools = None
        self.changeStyleWidget = None
        self.nextStyleAction = None
        self.prevStyleAction = None
        self.qgis.on('ReadProject', self.readProjectCallback)
        self.qgis.on('NewProject', self.createProjectCallback)
        self.loadedLayerIds = []
        self.acquisitionMenu = None
        self.validateUserOperations = self.spatialVerificationFactory.createVerification( 
            'ValidateUserOperations', 
            self.qgis 
        )
        self.workflowToolbox = None
        self.prodToolsSettings.reclassifyMode.connect(self.handleReclassifyMode)

        # Inicializa com o total de violação de regras em 1.
        self.total_rule_violations = 1

    def loadChangeStyleWidget(self):
        self.changeStyleWidget = self.guiFactory.getWidget('ChangeStyleWidget', controller=self)
        self.qgis.addWidgetToolBar(self.changeStyleWidget)
        self.changeStyleWidget.setEnabled(False)
        if not self.nextStyleAction: 
            self.nextStyleAction = self.qgis.createAction(
                'Próximo estilo',
                os.path.join(self.iconRootPath, 'nextStyle.png'),
                lambda:''
            )
            self.changeStyleWidget.setNextAction(self.nextStyleAction)   
            self.prodToolsSettings.addActionMenu(self.nextStyleAction)
        if not self.prevStyleAction: 
            self.prevStyleAction = self.qgis.createAction(
                'Último estilo',
                os.path.join(self.iconRootPath, 'prevStyle.png'),
                lambda:''
            )
            self.changeStyleWidget.setPrevAction(self.prevStyleAction)   
            self.prodToolsSettings.addActionMenu(self.prevStyleAction)

        return self.changeStyleWidget

    def closedDock(self):
        if not sip.isdeleted(self.changeStyleWidget):
            self.changeStyleWidget.clearStyles()
            self.changeStyleWidget.setEnabled(False)
        self.productionTools.close() if self.productionTools else ''
        
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

    def getPomodoroWidget(self):
        return self.pomodoro
        
    def unload(self):
        self.removeDock()
        self.qgis.off('ReadProject', self.readProjectCallback)
        self.qgis.off('NewProject', self.createProjectCallback)

    def reload(self):
        try:
            self.sapActivity = self.sap.getActivity()
            self.prodToolsSettings.checkPluginUpdates()
            if self.productionTools is None:
                return
            self.removeDock()
            self.sapActivity = self.sap.getActivity()
            if self.sapActivity is None:
                return
            self.loadShortcuts()
            self.productionTools = self.guiFactory.makeRemoteProductionToolsDock(self, self.productionTools)
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
                    QMessageBox.Ok
                )
                self.cleanupAfterNoActivities()
                self.closeOperatorWindow()
            else:
                QMessageBox.warning(
                    self.qgis.getMainWindow(),
                    "Erro",
                    f"Ocorreu um erro inesperado: {error_message}",
                    QMessageBox.Ok
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

    def loadShortcuts(self):
        shortcuts = self.sapActivity.getShortcuts()
        for shortcut in shortcuts:
            self.qgis.cleanDuplicateShortcut(shortcut['ferramenta'], shortcut['atalho'] if shortcut['atalho'] else '')
        for shortcut in shortcuts:
            self.qgis.setActionShortcut(shortcut['ferramenta'], shortcut['atalho'] if shortcut['atalho'] else '')

    def loadChangeStyleTool(self, stylesName):
        self.changeStyleWidget.setEnabled(True)
        self.changeStyleWidget.clearStyles()
        if not stylesName:
            return
        self.changeStyleWidget.loadStyles(stylesName, stylesName[0])
            
    def changeMapLayerStyle(self, styleName):
        self.qgis.changeMapLayerStyles(styleName)

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

    def removeDock(self):
        self.qgis.removeDockWidget(self.productionTools) if self.productionTools else ''
    
    def getShortcutQgisDescription(self):
        return self.sapActivity.getShortcutsDescription()

    def getActivityDescription(self):
        return self.sapActivity.getDescription()

    def getActivityLineage(self):
        return self.sapActivity.getLineage()

    def getActivityNotes(self):
        return self.sapActivity.getNotes()

    def getActivityRequirements(self):
        return self.sapActivity.getRequirements()

    def getActivityEPSG(self):
        return self.sapActivity.getEPSG()

    def getProject(self):
        return self.sapActivity.getProject()

    def getLot(self):
        return self.sapActivity.getLot()

    def getBlock(self):
        return self.sapActivity.getBlock()

    def getProductType(self):
        return self.sapActivity.getProductType()

    def getScale(self):
        return self.sapActivity.getScale()

    def getUserName(self):
        return self.sapActivity.getUserName()

    def getActivityStyles(self):
        return self.sapActivity.getStylesName()

    def showEndActivityDialog(self):
        if self.qgis.hasModifiedLayers():
            self.showInfoMessageBox(
                self.productionTools,
                'Aviso',
                'Salve todas suas alterações antes de finalizar!'
            )
            return
        if len(self.getDSGToolsQAWorkflows()) > 0 and (self.workflowToolbox is None or not self.workflowToolbox.allWorkflowsAreFinishedWithoutFlags()):
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

    def showReportErrorDialog(self):
        self.sap.showReportErrorDialog(
            self.resetProject
        )
    
    def resetProject(self):
        self.qgis.cleanProject()
        self.reload()
        
    def getActivityDatabase(self):
        return self.databaseFactory.createPostgres(
            self.sapActivity.getDatabaseName(), 
            self.sapActivity.getDatabaseServer(), 
            self.sapActivity.getDatabasePort(), 
            self.sapActivity.getDatabaseUserName(), 
            self.sapActivity.getDatabasePassword()
        )

    def getActivityLayerNames(self):
        return [
            item["nome"] for item in self.sapActivity.getLayers()
        ]

    def getActivityInputs(self):
        return self.sapActivity.getInputs()

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
        if rules != []:
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
        if rules != []:
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
                core.QgsWkbTypes.PointGeometry: [],
                core.QgsWkbTypes.LineGeometry: [],
                core.QgsWkbTypes.PolygonGeometry: [],
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
    
    def frameLoaded(self, frameQuery):
        layers = self.qgis.getLoadedVectorLayers()
        for l in layers:
            if not( l.source() == frameQuery ):
                continue
            return True
        return False

    def setLoadedLayerIds(self, loadedLayerIds):
        self.loadedLayerIds = loadedLayerIds

    def getLoadedLayerIds(self):
        return self.loadedLayerIds

    def getPathDest(self):
        return QtWidgets.QFileDialog.getExistingDirectory(
            self.productionTools if self.productionTools else utils.iface.mainWindow(), 
            u"Selecione pasta de destino dos insumos:",
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )

    def loadActivityInputs(self, inputData):
        results = []
        if not inputData:
            self.showInfoMessageBox(None, 'Aviso', 'Selecione o(s) insumo(s)!')
            return

        needPath = next((item for item in inputData if item["tipo_insumo_id"] == 1), None)
        if needPath:
            pathDest = self.getPathDest()
        for data in inputData:
            if data['tipo_insumo_id'] in [1]:
                if not pathDest:
                    continue
                data['caminho_padrao'] = pathDest
            result = self.qgis.loadInputData(data)
            results.append(result)
        return results

    def getActivityRoutines(self):
        fmeData = []
        #try:
        fmeData = self.fme.getSapRoutines(self.sapActivity.getFmeConfig())
        #except Exception as e:
        #    self.showErrorMessageBox(None, 'Erro', 'Sem conexão com o FME!')
        return self.sapActivity.getQgisModels() + self.sapActivity.getRuleRoutines() + fmeData

    def runRoutine(self, routineData):
        if not routineData:
            self.showInfoMessageBox(None, 'Aviso', 'Selecione uma rotina!')
            return
        if self.qgis.hasModifiedLayers():
            self.showHtmlMessageDialog(
                self.qgis.getMainWindow(),
                'Aviso',
                '''<p style="color:red">
                    Salve todas suas alterações antes de executar essa rotina!
                </p>'''
            )
            return
        rountineFunctions = {
            'rules': self.runRuleStatistics,
            'fme': self.runFMESAP,
            'qgisModel': self.runQgisModel
        }
        rountineFunctions[routineData['routineType']](routineData)

    def runFMESAP(self, routineData):
        runFMESAP = self.processingFactoryDsgTools.createProcessing('RunFMESAP', self)
        output = runFMESAP.run({
            'workUnitGeometry': self.sapActivity.getWorkUnitGeometry(),
            'fmeRoutine': routineData,
            'dbName': self.sapActivity.getDatabaseName(),
            'dbPort': self.sapActivity.getDatabasePort(),
            'dbHost': self.sapActivity.getDatabaseServer(),
            'dbUser': self.sapActivity.getDatabaseUserName(),
            'dbPassword': self.sapActivity.getDatabasePassword(),
            'sapSubfase': self.sapActivity.getSubphaseId()
        })
        summary = output['result']['dados']['sumario']
        html = "<p>[rotina nome] : {0}</p>".format(routineData['rotina'])
        html += "<p>[status de execução] : {0}</p>".format(output['result']['dados']['status'])
        for flags in output['result']['dados']['sumario']:
            html += """<p>[rotina flags] : {} - {}</p>""".format(flags['classes'], flags['feicoes'])
        self.showHtmlMessageDialog(
            self.qgis.getMainWindow(),
            'Aviso',
            html
        )

    def runRuleStatistics(self, routineData):
        ruleStatistics = self.processingFactoryDsgTools.createProcessing('RuleStatistics', self)
        result = ruleStatistics.run({
            'rules': routineData['ruleStatistics'],
            'layers': self.sapActivity.getLayers()
        })
        self.htmlMessageDlg = self.messageFactory.createMessage('RuleMessageDialog')
        self.htmlMessageDlg.show(
            self.qgis.getMainWindow(),
            'Aviso',
            result,
            self.qgis
        )
        # Calcula quantas violações de regras tem e armazena em self.total_rule_violations
        self.total_rule_violations =  len(result['[REGRAS] : Atributo incorreto']) + len(result['[REGRAS] : Preencher atributo'])
        
        return result

    def runQgisModel(self, routineData):
        html = self.qgis.runProcessingModel(routineData)
        QtWidgets.QApplication.restoreOverrideCursor()
        self.showHtmlMessageDialog(
            self.qgis.getMainWindow(),
            'Aviso',
            html
        )

    def showActivityDataSummary(self):
        dialog = self.guiFactory.makeActivitySummaryDialog(
            self,
            self.getActivityLayerNames(),
            self.sapActivity.getConditionalStyleNames()
        )
        dialog.exec_()

    def showHtmlMessageDialog(self, parent, title, message):
        self.htmlMessageDlg = self.messageFactory.createMessage('HtmlMessageDialog')
        self.htmlMessageDlg.show(parent, title, message)

    def showHtmlMessageDialog(self, parent, title, message):
        self.htmlMessageDlg = self.messageFactory.createMessage('HtmlMessageDialog')
        self.htmlMessageDlg.show(parent, title, message)

    def showInfoMessageBox(self, parent, title, message):
        messageDlg = self.messageFactory.createMessage('InfoMessageBox')
        messageDlg.show(parent, title, message)
    
    def showErrorMessageBox(self, parent, title, message):
        messageDlg = self.messageFactory.createMessage('ErrorMessageBox')
        messageDlg.show(parent, title, message)

    def readProjectCallback(self):
        self.productionTools.close() if self.productionTools else ''
        
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
        self.productionTools.close() if self.productionTools else ''
        self.canvasMonitoring.stop()

    def zoomToFeature(self, layerId, layerSchema, layerName):
        self.qgis.zoomToFeature(layerId, layerSchema, layerName)  
    
    def getSapMenus(self):
        return self.sapActivity.getMenus()

    def getDSGToolsQAWorkflows(self):
        return self.sapActivity.getWorkflows()

    def loadMenu(self):
        try:
            self.acquisitionMenu.removeMenuDock() if self.acquisitionMenu else ''
            customFeatureTool = self.toolFactoryDsgTools.getTool('CustomFeatureTool', self)
            self.acquisitionMenu = customFeatureTool.run( self.getSapMenus() )
        except Exception as e:
            self.showErrorMessageBox( None, 'Erro', str(e) )

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
        if candidateLayerList == []:
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
            if loadedLayerIds == []:
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


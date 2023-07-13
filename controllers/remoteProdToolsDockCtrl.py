
from Ferramentas_Producao.factories.GUIFactory import GUIFactory
from Ferramentas_Producao.factories.timerFactory import TimerFactory
from Ferramentas_Producao.factories.spatialVerificationFactory import SpatialVerificationFactory

from Ferramentas_Producao.controllers.prodToolsCtrl import ProdToolsCtrl
from PyQt5 import QtWidgets
from qgis import core, gui, utils

import os
import json
import sip

from Ferramentas_Producao.widgets.pomodoro import Pomodoro
from Ferramentas_Producao.monitoring.canvas import Canvas


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
            pomodoro=Pomodoro(),
            guiFactory=GUIFactory(),
            spatialVerificationFactory=SpatialVerificationFactory(),
            canvasMonitoring=Canvas()
        ):
        super(RemoteProdToolsDockCtrl, self).__init__()
        self.sap = sap
        self.qgis = qgis
        self.fme = fme
        self.pomodoro = pomodoro
        self.canvasMonitoring = canvasMonitoring
        self.canvasMonitoring.changeStatus.connect(self.pomodoro.setWorkStatusText)
        self.databaseFactory = databaseFactory
        self.processingFactoryDsgTools = processingFactoryDsgTools
        self.guiFactory = guiFactory
        self.spatialVerificationFactory = spatialVerificationFactory
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

    def closedDock(self):
        if not sip.isdeleted(self.changeStyleWidget):
            self.changeStyleWidget.clearStyles()
            self.changeStyleWidget.setEnabled(False)
        self.productionTools.close() if self.productionTools else ''
        
    def authUser(self, username, password, server):
        self.qgis.setProjectVariable('productiontools:user', username)
        self.qgis.setProjectVariable('productiontools:password', password)
        self.qgis.setSettingsVariable('productiontools:server', server)
        return self.sap.authUser(username, password, server)

    def getPomodoroWidget(self):
        return self.pomodoro
        
    def unload(self):
        self.removeDock()
        self.qgis.off('ReadProject', self.readProjectCallback)
        self.qgis.off('NewProject', self.createProjectCallback)
        #self.pomodoro.unload()

    def reload(self):
        self.prodToolsSettings.checkPluginUpdates()
        if self.productionTools is None:
            return
        self.removeDock()
        self.sapActivity = self.sap.getActivity()
        if self.sapActivity is None:
            return
        self.loadShortcuts()
        self.productionTools = self.guiFactory.makeRemoteProductionToolsDock(self, self.productionTools)
        self.qgis.addDockWidget(self.productionTools, side='left')  

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
        self.productionTools = self.guiFactory.makeRemoteProductionToolsDock(self)
        self.qgis.addDockWidget(self.productionTools, side='left')
        self.prodToolsSettings.checkPluginUpdates()  
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
        if stepTypeId == 3 and checkStep:
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
        return [item["nome"] for item in self.sapActivity.getLayers()]

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
            self.changeStyleWidget.loadStyles(self.getActivityStyles(), defaultStyle)

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

        assignAliasesToLayers = self.processingFactoryDsgTools.createProcessing('AssignAliasesToLayers', self)
        assignAliasesToLayers.run({
            'aliases': self.sapActivity.getLayerALiases(),
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

        """ assignConditionalStyleToLayers = self.processingFactoryDsgTools.createProcessing('AssignConditionalStyleToLayers', self)
        assignConditionalStyleToLayers.run({
            'conditionals': self.sapActivity.getLayerConditionalStyle(),
            'layerIds': loadedLayerIds
        }) """

        setRemoveDuplicateNodePropertyOnLayers = self.processingFactoryDsgTools.createProcessing('SetRemoveDuplicateNodePropertyOnLayers', self)
        setRemoveDuplicateNodePropertyOnLayers.run({'layerIds': loadedLayerIds})

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
        self.sap.reAuthUser()
        self.prodToolsSettings.checkPluginUpdates()
        self.productionTools.close() if self.productionTools else ''
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
        self.canvasMonitoring.stop()

    def zoomToFeature(self, layerId, layerSchema, layerName):
        self.qgis.zoomToFeature(layerId, layerSchema, layerName)  
    
    def getSapMenus(self):
        return self.sapActivity.getMenus()

    def loadMenu(self):
        try:
            self.acquisitionMenu.removeMenuDock() if self.acquisitionMenu else ''
            customFeatureTool = self.toolFactoryDsgTools.getTool('CustomFeatureTool', self)
            self.acquisitionMenu = customFeatureTool.run( self.getSapMenus() )
        except Exception as e:
            self.showErrorMessageBox( None, 'Erro', str(e) )
    
    def loadReviewTool(self):
        frameQuery = self.sapActivity.getFrameQuery()
        if not self.frameLoaded( frameQuery ):
            self.qgis.loadInputData({
                'query': self.sapActivity.getFrameQuery(),
                'epsg': self.sapActivity.getEPSG(),
                'nome': 'moldura',
                'tipo_insumo_id': 100,
                'qml': self.sapActivity.getFrameQml()
            })
        loadLayersFromPostgis = self.processingFactoryDsgTools.createProcessing('LoadLayersFromPostgis', self)
        result = loadLayersFromPostgis.run({ 
            'dbName' : self.sapActivity.getDatabaseName(), 
            'dbHost' : self.sapActivity.getDatabaseServer(), 
            'layerNames' : ['aux_grid_revisao_a'], 
            'dbPassword' : self.sapActivity.getDatabasePassword(), 
            'dbPort' : self.sapActivity.getDatabasePort(), 
            'dbUser' : self.sapActivity.getDatabaseUserName() 
        })
        loadedLayerIds = result['OUTPUT']
        if loadedLayerIds == []:
            return
        gridLayer = core.QgsProject.instance().mapLayer(loadedLayerIds[0])
        assingFilterToLayers = self.processingFactoryDsgTools.createProcessing('AssingFilterToLayers', self)
        assingFilterToLayers.run({
            'layers': [
                {
                    'filter': f'atividade_id = {self.sapActivity.getId()}',
                    'nome': 'aux_grid_revisao_a',
                    'schema': gridLayer.dataProvider().uri().schema()
                }
            ]
        })
        self.moveLayerToGroup(loadedLayerIds[0])
        reviewToolBar = self.toolFactoryDsgTools.getTool('ReviewToolBar', self)
        if gridLayer.featureCount() != 0:
            reviewToolBar.run(gridLayer)
            return
        createReviewGrid = self.processingFactoryDsgTools.createProcessing('CreateReviewGrid', self)
        result = createReviewGrid.run({
            'input': core.QgsProject.instance().mapLayersByName('moldura')[0],
            'x_grid_size': 0.01,
            'y_grid_size': 0.008,
            'related_task_id': self.sapActivity.getId()
        })
        outputLayer = result['OUTPUT']
        reviewToolBar.run(gridLayer, outputLayer=outputLayer)

    def moveLayerToGroup(self, loadedLayerId):
        utils.iface.mapCanvas().freeze(True)
        rootNode = core.QgsProject.instance().layerTreeRoot()
        group = rootNode.findGroup('MOLDURA_E_INSUMOS')
        lyrNode = rootNode.findLayer(loadedLayerId)
        myClone = lyrNode.clone()
        group.insertChildNode(0, myClone)
        rootNode.removeChildNode(lyrNode)
        utils.iface.mapCanvas().freeze(False)

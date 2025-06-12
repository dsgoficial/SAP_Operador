
from collections import OrderedDict
from SAP_Operador.factories.GUIFactory import GUIFactory
from SAP_Operador.factories.timerFactory import TimerFactory
from SAP_Operador.factories.spatialVerificationFactory import SpatialVerificationFactory

from SAP_Operador.controllers.prodToolsCtrl import ProdToolsCtrl
from PyQt5 import QtWidgets
from qgis import core, gui, utils

import os
import json
import sip

from SAP_Operador.widgets.pomodoro import Pomodoro
from SAP_Operador.monitoring.canvas import Canvas
from SAP_Operador.postgresql import Postgresql
import psycopg2

class LocalProdToolsDockCtrl(ProdToolsCtrl):

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
        super(LocalProdToolsDockCtrl, self).__init__()
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
        if self.changeStyleWidget and not sip.isdeleted(self.changeStyleWidget):
            self.changeStyleWidget.clearStyles()
            self.changeStyleWidget.setEnabled(False)
        self.productionTools.close() if self.productionTools else ''
        
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
            return False
        result = pg.execute(
            '''
                SELECT count(*) FROM public.sap_local;
            ''',
            ()
        )
        if result[0][0] == 0:
            raise Exception('Não há dados na tabela "public.sap_local"!')
            return False
        return True

    def getPomodoroWidget(self):
        return self.pomodoro
        
    def unload(self):
        self.removeDock()
        self.qgis.off('ReadProject', self.readProjectCallback)
        self.qgis.off('NewProject', self.createProjectCallback)
        #self.pomodoro.unload()

    def reload(self):
        #self.prodToolsSettings.checkPluginUpdates()
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

    def loadDockWidget(self, dbusername, dbpassword, dbhost, dbport, dbname):
        pg = Postgresql(dbname, dbusername, dbhost, dbport, dbpassword)
        result = pg.execute(
            '''
                SELECT json_atividade FROM public.sap_local;
            ''',
            ()
        )
        activityData = json.loads(result[0][0])
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
        #self.resetProject()

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
            if lyr.name() in ("aux_grid_revisao_a", "moldura"):
                idx = 0 if "aux_grid_revisao_a" else -1
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
        self.prodToolsSettings.initSaveTimer()
        self.canvasMonitoring.start()

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
        if not self.frameLoaded(frameQuery):
            self.qgis.loadInputData({
                'query': self.sapActivity.getFrameQuery(),
                'epsg': self.sapActivity.getEPSG(),
                'nome': 'moldura',
                'tipo_insumo_id': 100,
                'qml': self.sapActivity.getFrameQml()
            })
        loadLayersFromPostgis = self.processingFactoryDsgTools.createProcessing('LoadLayersFromPostgis', self)
        gridCandidateList = core.QgsProject.instance().mapLayersByName('aux_grid_revisao_a')
        if gridCandidateList == []:
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
            gridLayer = gridCandidateList[0]

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
        
        self.moveLayerToGroup(loadedLayerIds[0])

        reviewToolBar = self.toolFactoryDsgTools.getTool('ReviewToolBar', self)
        if gridLayer.featureCount() != 0:
            reviewToolBar.run(gridLayer)
            return

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

        # Add appropriate IDs based on field existence
        if has_new_fields:
            param.update({
                'unit_work_id': self.sapActivity.getWorkUnitId(),
                'step_id': self.sapActivity.getStepId()
            })
        else:
            param['related_task_id'] = self.sapActivity.getId()

        result = createReviewGrid.run(param)
        outputLayer = result['OUTPUT']
        reviewToolBar.run(gridLayer, outputLayer=outputLayer)

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

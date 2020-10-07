
from Ferramentas_Producao.factories.GUIFactory import GUIFactory
from Ferramentas_Producao.factories.timerFactory import TimerFactory

import os

class ProductionToolsCtrl:
    
    def __init__(
            self,
            sap,
            qgis,
            databaseFactory,
            processingFactory,
            fme,
            messageFactory,
            pomodoro,
            guiFactory=GUIFactory(),
            timerFactory=TimerFactory()
        ):
        self.sap = sap
        self.qgis = qgis
        self.fme = fme
        self.databaseFactory = databaseFactory
        self.processingFactory = processingFactory
        self.guiFactory = guiFactory
        self.timerFactory = timerFactory
        self.messageFactory = messageFactory
        self.pomodoro = pomodoro
        self.sapActivity = None
        self.productionTools = None
        self.saveTimer = None
        self.hideLayer = True
        self.showMarkers = True
        self.menuBarActions = []
        self.qgis.on('readProject', self.readProjectCallback)
        self.loadCustomQgisSettings()
        self.createActionsMenuBar()
        self.createMenuBar()
    
    def createActionsMenuBar(self):
        menuBarActions = []
        for actionConfig in self.getMenuBarActionSettings():
            action = self.qgis.createAction(
                actionConfig['name'],
                actionConfig['iconPath'],
                actionConfig['callback'],
                actionConfig['shortcut']
            )
            menuBarActions.append(action)
        self.setMenuBarActions(menuBarActions)

    def setMenuBarActions(self, menuBarActions):
        self.menuBarActions = menuBarActions

    def getMenuBarActions(self):
        return self.menuBarActions

    def getPomodoroWidget(self):
        return self.pomodoro.getWidget()

    def createMenuBar(self):
        self.menuBarMain = self.qgis.addMenuBar('Ferramentas de Produção')
        for action in self.getMenuBarActions():
            self.menuBarMain.addAction(action)
        
    def unload(self):
        self.removeDock()
        for action in self.getMenuBarActions():
            self.menuBarMain.removeAction(action)
        self.setMenuBarActions([])
        self.qgis.off('readProject', self.readProjectCallback)

    def reload(self):
        if self.productionTools is None:
            return
        self.sapActivity = self.sap.getActivity()
        if self.sapActivity is None:
            self.removeDock()
            return
        self.productionTools = self.guiFactory.makeProductionToolsDock(self, self.productionTools)

    def loadDockWidget(self, sapActivity=None):
        self.sapActivity = self.sap.getActivity() if sapActivity is None else sapActivity
        if not self.sapActivity:
            return
        self.productionTools = self.guiFactory.makeProductionToolsDock(self)
        self.qgis.addDockWidget(self.productionTools, side='left')        

    def removeDock(self):
        self.qgis.removeDockWidget(self.productionTools) if self.productionTools else ''
        
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

    def getUserName(self):
        return self.sapActivity.getUserName()

    def getActivityStyles(self):
        return self.sapActivity.getStylesName()

    def showEndActivityDialog(self, sender):
        if self.qgis.hasModifiedLayers():
            self.showInfoMessageBox(
                self.productionTools,
                'Aviso',
                'Salve todas suas alterações antes de finalizar!'
            )
            return
        self.sap.showEndActivityDialog(self.reload)

    def showReportErrorDialog(self, sender):
        self.sap.showReportErrorDialog(self.reload)

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

    def loadActivityLayers(self, sender):
        onlyWithFeatures = sender.onlyWithFeatures()
        styleName = sender.getStyle()
        loadLayersFromPostgis = self.processingFactory.createProcessing('LoadLayersFromPostgis', self)
        result = loadLayersFromPostgis.run({ 
            'dbName' : self.sapActivity.getDatabaseName(), 
            'dbHost' : self.sapActivity.getDatabaseServer(), 
            'layerNames' : self.getActivityLayerNames(), 
            'dbPassword' : self.sapActivity.getDatabasePassword(), 
            'dbPort' : self.sapActivity.getDatabasePort(), 
            'dbUser' : self.sapActivity.getDatabaseUserName() 
        })
        loadedLayerIds = result['OUTPUT']

        assingFilterToLayers = self.processingFactory.createProcessing('AssingFilterToLayers', self)
        assingFilterToLayers.run({'layers': self.sapActivity.getLayers()})
    
        if onlyWithFeatures:
            self.qgis.removeLayersWithouFeatures(loadedLayerIds)

        groupLayers = self.processingFactory.createProcessing('GroupLayers', self)
        groupLayers.run({'layerIds': loadedLayerIds})

        matchAndApplyQmlStylesToLayers = self.processingFactory.createProcessing('MatchAndApplyQmlStylesToLayers', self)
        matchAndApplyQmlStylesToLayers.run({
            'layersQml': self.sapActivity.getLayersQml(styleName),
            'layerIds': loadedLayerIds
        })

        assignValueMapToLayers = self.processingFactory.createProcessing('AssignValueMapToLayers', self)
        database = self.getActivityDatabase()
        assignValueMapToLayers.run({
            'valueMaps': {
                    layer["nome"]: database.getAttributeValueMap(layer["nome"], layer["schema"])
                    for layer in self.sapActivity.getLayers()
            },
            'layerIds': loadedLayerIds
        }) 

        assignMeasureColumnToLayers = self.processingFactory.createProcessing('AssignMeasureColumnToLayers', self)
        assignMeasureColumnToLayers.run({'layerIds': loadedLayerIds})

        assignAliasesToLayers = self.processingFactory.createProcessing('AssignAliasesToLayers', self)
        assignAliasesToLayers.run({
            'aliases': self.sapActivity.getLayerALiases(),
            'layerIds': loadedLayerIds
        })

        assignActionsToLayers = self.processingFactory.createProcessing('AssignActionsToLayers', self)
        assignActionsToLayers.run({
            'actions': self.sapActivity.getLayerActions(),
            'layerIds': loadedLayerIds
        })

        assignDefaultFieldValueToLayers = self.processingFactory.createProcessing('AssignDefaultFieldValueToLayers', self)
        assignDefaultFieldValueToLayers.run({
            'defaultValues': self.sapActivity.getLayerDefaultFieldValue(),
            'layerIds': loadedLayerIds
        })

        assignExpressionFieldToLayers = self.processingFactory.createProcessing('AssignExpressionFieldToLayers', self)
        assignExpressionFieldToLayers.run({
            'expressions': self.sapActivity.getLayerExpressionField(),
            'layerIds': loadedLayerIds
        })

        assignConditionalStyleToLayers = self.processingFactory.createProcessing('AssignConditionalStyleToLayers', self)
        assignConditionalStyleToLayers.run({
            'conditionals': self.sapActivity.getLayerConditionalStyle(),
            'layerIds': loadedLayerIds
        })

        self.qgis.loadInputData({
            'query': self.sapActivity.getFrameQuery(),
            'nome': 'moldura',
            'tipo_insumo_id': 100,
            'qml': self.sapActivity.getFrameQml()
        })
        
        self.qgis.loadLayerActions(loadedLayerIds)
        
        self.initSaveTimer()

    def loadActivityInputs(self, sender):
        inputData = sender.getInputsSelected()
        if not inputData:
            return
        for data in inputData:
            self.qgis.loadInputData(data)

    def getActivityRoutines(self):
        return self.sapActivity.getQgisModels() + self.sapActivity.getRuleRoutines() + self.fme.getSapRoutines(self.sapActivity.getFmeConfig())

    def runRoutine(self, sender):
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
        routineData = sender.getRoutineSelected()
        html = rountineFunctions[routineData['routineType']](routineData)
        self.showHtmlMessageDialog(
            self.qgis.getMainWindow(),
            'Aviso',
            html
        )
        #self.qgis.setSettingsVariable('productiontools:user', user)
        #self.qgis.getSettingsVariable('productiontools:user')

    def runFMESAP(self, routineData):
        runFMESAP = self.processingFactory.createProcessing('RunFMESAP', self)
        return runFMESAP.run({
            'workUnitGeometry': self.sapActivity.getWorkUnitGeometry(),
            'fmeRoutine': routineData,
            'dbName': self.sapActivity.getDatabaseName(),
            'dbPort': self.sapActivity.getDatabasePort(),
            'dbHost': self.sapActivity.getDatabaseServer()
        })

    def runRuleStatistics(self, routineData):
        ruleStatistics = self.processingFactory.createProcessing('RuleStatistics', self)
        return ruleStatistics.run({
            'rules': routineData,
            'layers': self.sapActivity.getLayers()
        })

    def runQgisModel(self, routineData):
        return self.qgis.runProcessingModel(routineData)

    def notify(self, sender, event):
        eventFunctions = {
            'endActivity': self.showEndActivityDialog,
            'errorActivity': self.showReportErrorDialog,
            'loadActivityLayers': self.loadActivityLayers,
            'runRoutine': self.runRoutine,
            'showActivityDataSummary': self.showActivityDataSummary,
            'loadActivityInputs': self.loadActivityInputs
        }
        eventFunctions[event](sender)

    def showActivityDataSummary(self, sender):
        dialog = self.guiFactory.makeActivitySummaryDialog(
            self,
            self.getActivityLayerNames(),
            self.sapActivity.getConditionalStyleNames()
        )
        dialog.exec_()

    def showHtmlMessageDialog(self, parent, title, message):
        htmlMessageDlg = self.messageFactory.createMessage('HtmlMessageDialog')
        htmlMessageDlg.show(parent, title, message)

    def showInfoMessageBox(self, parent, title, message):
        messageDlg = self.messageFactory.createMessage('InfoMessageBox')
        messageDlg.show(parent, title, message)
    
    def showErrorMessageBox(self, parent, title, message):
        messageDlg = self.messageFactory.createMessage('ErrorMessageBox')
        messageDlg.show(parent, title, message)

    def readProjectCallback(self):
        if self.sap.isValidActivity():
            self.initSaveTimer()
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

    def initSaveTimer(self):
        if self.saveTimer:
            self.saveTimer.reset()
            return
        self.saveTimer = self.timerFactory.createTimer('Timer')
        self.saveTimer.addCallback(self.saveMessage)
        self.saveTimer.start(1000*60*5)
        self.qgis.on('SaveAllEdits', self.saveTimer.reset)
        self.qgis.on('SaveActiveLayerEdits', self.saveTimer.reset)

    def freeHandIsActive(self):
        freeHandStrClass = "<class 'DsgTools.gui.ProductionTools.MapTools.FreeHandTool.models.acquisitionFree.AcquisitionFree'>"
        return str(type(self.qgis.getCurrentMapTool())) == freeHandStrClass

    def haveToSave(self):
        return (
            self.qgis.hasModifiedLayers()
            and
            not(self.freeHandIsActive())
        )

    def saveMessage(self):
        if not self.haveToSave():
            return
        self.showInfoMessageBox(
            self.qgis.getMainWindow(),
            'Aviso',
           '<p style="color:red">Salve suas alterações!</p>'
        )
    
    def loadCustomQgisSettings(self):
        settings = self.getCustomQgisSettings()
        self.qgis.cleanShortcuts(settings)
        self.qgis.setSettings(settings)
        self.qgis.cleanActionShortcut('EnableSnappingAction')

    def onOffLayers(self):
        self.qgis.setHiddenLayers(self.hideLayer)
        self.hideLayer = not self.hideLayer

    def showMarkersOnlySelectedFeatures(self):
        values = {
            True: 'true',
            False: 'false'
        }
        self.qgis.setSettings({
            'qgis/digitizing/marker_only_for_selected': values[self.showMarkers]
        })
        self.qgis.canvasRefresh()
        self.showMarkers = not self.showMarkers

    def getShortcutQgisDescription(self):
        descriptionHtml = ''
        customQgisSettings = self.getCustomQgisSettings()
        for settingsKey in customQgisSettings:
            if not('shortcuts' in settingsKey.lower()):
                continue
            if not(customQgisSettings[settingsKey]):
                continue
            descriptionHtml += '<b>{0}:</b> {1}<br>'.format(
                settingsKey.split('/')[1], 
                customQgisSettings[settingsKey]
            )
        return '<div>{0}</div>'.format(descriptionHtml)

    def smoothLine(self):
        #result = self.qgis.smoothLine()
        result = self.qgis.runMapFunctions([{'name': 'SmoothLine'}])
        if not result[0]:
            self.showErrorMessageBox(
                self.qgis.getMainWindow(),
                'Erro',
                '<p style="color:red">{0}</p>'.format(result[1])
            )

    def closeLine(self):
        #result = self.qgis.closeLine()
        result = self.qgis.runMapFunctions([{'name': 'CloseLine'}])
        if not result[0]:
            self.showErrorMessageBox(
                self.qgis.getMainWindow(),
                'Erro',
                '<p style="color:red">{0}</p>'.format(result[1])
            )

    def pageRaster(self, direction):
        result = self.qgis.pageRaster(direction)
        if not result[0]:
            self.showErrorMessageBox(
                self.qgis.getMainWindow(),
                'Erro',
                '<p style="color:red">{0}</p>'.format(result[1])
            )

    def getMenuBarActionSettings(self):
        iconRootPath = os.path.join(
                os.path.dirname(__file__),
                'icons'
        )
        return [
            {
                'name': 'Ligar/Desligar camada',
                'iconPath':os.path.join(iconRootPath, 'on_off.png'),
                'shortcut': 'Y',
                'callback': self.onOffLayers
            },
            {
                'name': 'Mostrar/Esconder marcadores para feições selecionadas',
                'iconPath':os.path.join(iconRootPath, 'vertex.png'),
                'shortcut': 'B',
                'callback': self.showMarkersOnlySelectedFeatures
            },
            {
                'name': 'Suavizador de linhas',
                'iconPath':os.path.join(iconRootPath, 'smoothLayer.png'),
                'shortcut': '',
                'callback': self.smoothLine
            },
            {
                'name': 'Fechar linha',
                'iconPath':os.path.join(iconRootPath, 'closeLine.png'),
                'shortcut': '',
                'callback': self.closeLine
            },
            {
                'name': 'Aparar linha',
                'iconPath':os.path.join(iconRootPath, 'trim.png'),
                'shortcut': '',
                'callback': lambda: self.qgis.activeTool('TrimLineMapTool')
            },
            {
                'name': 'Expandir linha',
                'iconPath':os.path.join(iconRootPath, 'expand.png'),
                'shortcut': '',
                'callback': lambda: self.qgis.activeTool('ExpandLineMapTool')
            },
            {
                'name': 'Paginar raster para cima',
                'iconPath':os.path.join(iconRootPath, 'pageup.png'),
                'shortcut': '',
                'callback': lambda direction='up': self.pageRaster(direction)
            },
            {
                'name': 'Paginar raster para baixo',
                'iconPath':os.path.join(iconRootPath, 'pagedown.png'),
                'shortcut': '',
                'callback': lambda direction='down': self.pageRaster(direction)
            },
            {
                'name': 'Criar nova visualização de mapa',
                'iconPath':os.path.join(iconRootPath, 'newmapview.png'),
                'shortcut': '',
                'callback': lambda: self.qgis.createNewMapView()
            },
            {
                'name': 'Convergir vertices de feições',
                'iconPath':os.path.join(iconRootPath, 'convergencepoint.png'),
                'shortcut': '',
                'callback': lambda: self.qgis.activeTool('ConvergencePoint')
            },
        ]

    def getCustomQgisSettings(self):
        return {
            u'qgis/parallel_rendering' : u'true',
            u'qgis/max_threads' : 8,
            u'qgis/simplifyDrawingHints': u'0',            
            u'qgis/digitizing/marker_only_for_selected' : u'false',
            'qgis/digitizing/default_snapping_tolerance' : '10',
            'qgis/digitizing/default_snap_enabled' : 'true', 
            u'qgis/digitizing/default_snap_type' : u'Vertex',
            'Map/scales' : '1:250000,1:100000,1:50000,1:25000,1:10000,1:5000,1:2000,1:1000,1:500,1:250',
            'qgis/digitizing/line_width' : '3',
            'qgis/digitizing/line_color_alpha' : '63',
            'qgis/digitizing/fill_color_alpha' : '40',
            u'qgis/default_selection_color_alpha': u'63',
            u'shortcuts/Sair do QGIS' : u'',
            u'shortcuts/Exit QGIS' : u'',
            u'shortcuts/Mesclar fei\xe7\xf5es selecionadas' : u'M',
            u'shortcuts/Merge Selected Features' : u'M',
            u'shortcuts/Quebrar Fei\xe7\xf5es' : u'C',
            u'shortcuts/Split Features' : u'C',
            u'shortcuts/Identificar fei\xe7\xf5es': u'I',
            u'shortcuts/Identify Features': u'I',
            u'shortcuts/Adicionar fei\xe7\xe3o': u'A',
            u'shortcuts/Add Feature': u'A',
            u'shortcuts/Desfazer sele\xe7\xe3o de fei\xe7\xf5es em todas as camadas': u'D',
            u'shortcuts/Deselect Features from All Layers': u'D',
            u'shortcuts/Ferramenta Vértice (Todas as Camadas)' : u'N',
            u'shortcuts/Vertex Tool (All Layers)' : u'N',
            u'shortcuts/Salvar para todas as camadas' : u'Ctrl+S',
            u'shortcuts/Save for All Layers' : u'Ctrl+S',
            u'shortcuts/Habilitar tra\xe7ar' : u'T',
            u'shortcuts/Enable Tracing' : u'T',
            u'shortcuts/Remodelar fei\xe7\xf5es' : u'R',
            u'shortcuts/Reshape Features' : u'R',
            u'shortcuts/\xc1rea' : u'Z',
            u'shortcuts/Measure Area' : u'Z',
            u'shortcuts/Linha' : u'X',
            u'shortcuts/Measure Line' : u'X',
            u'shortcuts/DSGTools: Generic Selector': u'S',
            u'shortcuts/DSGTools: Seletor Gen\xe9rico': u'S',
            u'shortcuts/DSGTools: Right Degree Angle Digitizing': u'E',
            u'shortcuts/DSGTools: Ferramenta de aquisi\xe7\xe3o com \xe2ngulos retos': u'E',
            'shortcuts/Topological Editing' : 'H',
            u'shortcuts/Salvar' : u'',
            u'shortcuts/Save' : u'',
            u'shortcuts/Select Feature(s)' : u'V',
            u'shortcuts/Fei\xe7\xe3o(s)' : u'V',
            u'shortcuts/DSGTools: Inspecionar anterior': u'Q',
            u'shortcuts/DSGTools: Back Inspect': u'Q',
            u'shortcuts/DSGTools: Inspecionar pr\xf3ximo': u'W',
            u'shortcuts/DSGTools: Next Inspect': u'W',
            u'shortcuts/DSGTools: Desenhar Forma': u'G',
            u'shortcuts/DSGTools: Draw Shape': u'G',
            u'shortcuts/Desfazer' : u'',
            u'shortcuts/Undo' : u'',
            u'shortcuts/Undo' : u'',
            u'shortcuts/Mostrar camadas selecionadas' : u'',
            u'shortcuts/Show Selected Layers' : u'',
            u'shortcuts/Esconder camadas selecionadas' : u'',
            u'shortcuts/Hide Selected Layers' : u'',
            u'shortcuts/Toggle Snapping' : u'',
            'shortcuts/DSGTools: Toggle all labels visibility' : 'L',
            u'shortcuts/DSGTools: Ferramenta de Aquisição à Mão Livre' : 'F',
            'shortcuts/DSGTools: Free Hand Acquisition' : 'F',
            'shortcuts/DSGTools: Free Hand Reshape' : 'Shift+R'
        }

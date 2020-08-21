
from Ferramentas_Producao.factories.GUIFactory import GUIFactory
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
            guiFactory=GUIFactory()
        ):
        self.guiFactory = guiFactory
        self.sap = sap
        self.qgis = qgis
        self.databaseFactory = databaseFactory
        self.processingFactory = processingFactory
        self.fme = fme
        self.messageFactory = messageFactory
        self.sapActivity = None
        self.productionTools = None
        self.qgis.on('readProject', self.readProjectCallback)
        self.loadCustomQgisSettings()

    def unload(self):
        self.removeDock()
        self.qgis.deleteAction(self.actionOnOffLayer)
        self.qgis.deleteAction(self.actionShowHideVertex)
        self.qgis.off('readProject', self.readProjectCallback)

    def reload(self):
        self.loadDockWidget()

    def loadDockWidget(self):
        self.sapActivity = self.sap.getActivity()
        if not self.sapActivity:
            return
        self.removeDock()
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

    def getUserName(self):
        return self.sapActivity.getUserName()

    def getActivityStyles(self):
        return self.sapActivity.getStylesName()

    def showEndActivityDialog(self, sender):
        if self.qgis.hasModifiedLayers():
            self.showBoxInfo(
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

    def loadActivityData(self, sender):
        onlyWithFeatures = sender.onlyWithFeatures(),
        notLoadInputs = sender.notLoadInputs(),
        styleName = sender.getStyle()
        loadLayersFromPostgis = self.processingFactory.createProcessing('LoadLayersFromPostgis', self)
        result = loadLayersFromPostgis.run({ 
            'dbName' : self.sapActivity.getDatabaseName(), 
            'dbHost' : self.sapActivity.getDatabaseServer(), 
            'layerNames' : [item["nome"] for item in self.sapActivity.getLayers()], 
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
        if notLoadInputs:
            return
        for data in self.sapActivity.getInputs():
            self.qgis.loadInputData(data)

    def openRoutinesDialog(self, sender):
        routinesDialog = self.guiFactory.makeRoutinesDialog(self, self.productionTools)
        routinesDialog.addRountines(
            self.sapActivity.getQgisModels() +
            self.sapActivity.getRuleRoutines() +
            self.fme.getSapRoutines(self.sapActivity.getFmeConfig())
        )
        routinesDialog.exec_()

    def runRoutine(self, sender):
        if self.qgis.hasModifiedLayers():
            self.showHTMLInfo(
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
        routineData = sender.getCurrentRoutineData()
        html = rountineFunctions[routineData['routineType']](routineData)
        self.showHTMLInfo(
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
            'loadActivity': self.loadActivityData,
            'openRoutines': self.openRoutinesDialog,
            'runRoutine': self.runRoutine,
        }
        eventFunctions[event](sender)

    def showHTMLInfo(self, title, message):
        htmlMessageDlg = self.messageFactory.createHTMLMessageDialog()
        htmlMessageDlg.show(parent, title, message)

    def showBoxInfo(self, parent, title, message):
        htmlMessageDlg = self.messageFactory.createHTMLMessageDialog()
        htmlMessageDlg.show(parent, title, message)

    def readProjectCallback(self):
        pass

    def loadCustomQgisSettings(self):
        settings = self.getCustomQgisSettings()
        self.qgis.cleanShortcuts(settings)
        self.qgis.setSettings(settings)
        self.qgis.cleanActionShortcut('EnableSnappingAction')
        self.actionOnOffLayer = self.qgis.createAction(
            'Ligar/Desligar camada',
            os.path.join(
                os.path.dirname(__file__),
                'icons',
                'on_off.png'
            ),
            'Y',
            self.onOffLayers
        )
        self.actionShowHideVertex = self.qgis.createAction(
            'Mostrar/Esconder marcadores para feições selecionadas',
            os.path.join(
                os.path.dirname(__file__),
                'icons',
                'vertex.png'
            ),
            'B',
            self.showMarkersOnlySelectedFeatures
        )

    def onOffLayers(self, b):
        self.qgis.setHiddenLayers(b)

    def showMarkersOnlySelectedFeatures(self, b):
        if b:
            self.qgis.setSettings([{
                'qgis/digitizing/marker_only_for_selected': 'true'
            }])
        else:
            self.qgis.setSettings([{
                'qgis/digitizing/marker_only_for_selected': 'false'
            }])
        self.qgis.canvasRefresh()

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

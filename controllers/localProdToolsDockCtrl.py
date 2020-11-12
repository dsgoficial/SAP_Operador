
from Ferramentas_Producao.factories.GUIFactory import GUIFactory
from Ferramentas_Producao.factories.timerFactory import TimerFactory
from Ferramentas_Producao.controllers.prodToolsCtrl import ProdToolsCtrl

import os

class LocalProdToolsDockCtrl(ProdToolsCtrl):
    
    def __init__(
            self,
            sap,
            qgis,
            databaseFactory,
            processingFactory,
            prodToolsSettings,
            guiFactory=GUIFactory()
        ):
        super(LocalProdToolsDockCtrl, self).__init__()
        self.sap = sap
        self.qgis = qgis
        self.databaseFactory = databaseFactory
        self.processingFactory = processingFactory
        self.guiFactory = guiFactory
        self.prodToolsSettings = prodToolsSettings
        self.sapActivity = None
        self.productionTools = None
        self.qgis.on('readProject', self.readProjectCallback)

    def readProjectCallback(self):
        self.prodToolsSettings.initSaveTimer()

    def authUser(self, dbusername, dbpassword, dbhost, dbport, dbname):
        return self.sap.authUser(dbusername, dbpassword, dbhost, dbport, dbname)
        
    def unload(self):
        self.removeDock()

    def closedDock(self):
        pass

    def loadDockWidget(self):
        self.sapActivity = self.sap.getActivity()
        if not self.sapActivity:
            return
        self.productionTools = self.guiFactory.makeLocalProductionToolsDock(self)
        self.qgis.addDockWidget(self.productionTools, side='left')        

    def removeDock(self):
        self.qgis.removeDockWidget(self.productionTools) if self.productionTools else ''

    def getActivityLayers(self):
        return self.sapActivity.getLayerNames()

    def getActivityStyles(self):
        return self.sapActivity.getStyleNames()

    def getActivityWorkspaces(self):
        return self.sapActivity.getWorkspaceNames()

    def getActivityDatabase(self):
        return self.databaseFactory.createPostgres(
            self.sapActivity.getDatabaseName(), 
            self.sapActivity.getDatabaseServer(), 
            self.sapActivity.getDatabasePort(), 
            self.sapActivity.getDatabaseUserName(), 
            self.sapActivity.getDatabasePassword()
        )

    def loadActivityLayers(self, layerNames, workspaceNames, onlyWithFeatures, styleName):
        loadLayersFromPostgis = self.processingFactory.createProcessing('LoadLayersFromPostgis', self)
        result = loadLayersFromPostgis.run({ 
            'dbName' : self.sapActivity.getDatabaseName(), 
            'dbHost' : self.sapActivity.getDatabaseServer(), 
            'layerNames' : layerNames, 
            'dbPassword' : self.sapActivity.getDatabasePassword(), 
            'dbPort' : self.sapActivity.getDatabasePort(), 
            'dbUser' : self.sapActivity.getDatabaseUserName() 
        })
        loadedLayerIds = result['OUTPUT']

        if workspaceNames:
            assingFilterToLayers = self.processingFactory.createProcessing('AssingFilterToLayers', self)
            assingFilterToLayers.run({'layers': self.sapActivity.getLayersFilter(workspaceNames)})
    
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
        ###
        """ self.qgis.loadInputData({
            'query': self.sapActivity.getFrameQuery(),
            'nome': 'moldura',
            'tipo_insumo_id': 100,
            'qml': self.sapActivity.getFrameQml()
        }) """
        
        self.qgis.loadLayerActions(loadedLayerIds)
        self.prodToolsSettings.initSaveTimer()

    def getActivityRoutines(self):
        return self.sapActivity.getQgisModels() + self.sapActivity.getRuleRoutines()

    def runRoutine(self, routineData):
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
            'qgisModel': self.runQgisModel
        }
        html = rountineFunctions[routineData['routineType']](routineData)
        self.showHtmlMessageDialog(
            self.qgis.getMainWindow(),
            'Aviso',
            html
        )
        #self.qgis.setSettingsVariable('productiontools:user', user)
        #self.qgis.getSettingsVariable('productiontools:user')

    def runRuleStatistics(self, routineData):
        ruleStatistics = self.processingFactory.createProcessing('RuleStatistics', self)
        return ruleStatistics.run({
            'rules': routineData,
            'layers': self.sapActivity.getLayers()
        })

    def runQgisModel(self, routineData):
        return self.qgis.runProcessingModel(routineData)

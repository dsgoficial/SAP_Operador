from Ferramentas_Producao.modules.qgis.interfaces.IQgisCtrl import IQgisCtrl
from Ferramentas_Producao.modules.qgis.factories.qgisApiSingleton import QgisApiSingleton
from qgis.utils import iface


class QgisCtrl(IQgisCtrl):

    def __init__(
            self,
            apiQGis=QgisApiSingleton.getInstance()
        ):
        super(QgisCtrl, self).__init__()
        self.apiQGis = apiQGis

    def getMainWindow(self):
        return self.apiQGis.getMainWindow()

    def setProjectVariable(self, key, value):
        self.apiQGis.setProjectVariable(key, value)

    def getProjectVariable(self, key):
        return self.apiQGis.getProjectVariable(key)

    def setSettingsVariable(self, key, value):
        self.apiQGis.setSettingsVariable(key, value)

    def getSettingsVariable(self, key):
        return self.apiQGis.getSettingsVariable(key)

    def getVersion(self):
        return self.apiQGis.getVersion()

    def getPluginsVersions(self):
        return self.apiQGis.getPluginsVersions()

    def addDockWidget(self, dockWidget, side='right'):
        self.apiQGis.addDockWidget(dockWidget, side)

    def removeDockWidget(self, dockWidget):
        self.apiQGis.removeDockWidget(dockWidget)
    
    def addActionDigitizeToolBar(self, action):
        self.apiQGis.addActionDigitizeToolBar(action)
    
    def removeActionDigitizeToolBar(self, action):
        self.apiQGis.removeActionDigitizeToolBar(action)

    def hasModifiedLayers(self):
        return self.apiQGis.hasModifiedLayers()

    def runProcessingModel(self, parametersData):
        return self.apiQGis.runProcessingModel(parametersData)

    def loadInputData(self, inputData):
        self.apiQGis.loadInputData(inputData)

    def removeLayersWithouFeatures(self, layerIds):
        self.apiQGis.removeLayersWithouFeatures(layerIds)

    def getLayerUriFromId(self, layerId):
        return self.apiQGis.getLayerUriFromId(layerId)
           
    def getLayerUriFromTable(self, layerSchema, layerName):
        return self.apiQGis.getLayerUriFromTable(layerSchema, layerName)

    def setSettings(self, settings):
        self.apiQGis.setSettings(settings)

    def cleanShortcuts(self,settings):
        self.apiQGis.cleanShortcuts(settings)

    def cleanActionShortcut(self, actionName):
        self.apiQGis.cleanActionShortcut(actionName)

    def addMenuBar(self, name):
        return self.apiQGis.addMenuBar(name)

    def addActionDigitizeToolBar(self, action):
        self.apiQGis.addActionDigitizeToolBar(action)

    def removeActionDigitizeToolBar(self, action):
        self.apiQGis.removeActionDigitizeToolBar(action)
    
    def createAction(self, name, iconPath, callback, shortcutKeyName='', checkable=False):
        return self.apiQGis.createAction(name, iconPath, callback, shortcutKeyName, checkable)

    def deleteAction(self, action):
        self.apiQGis.deleteAction(action)

    def setHiddenLayers(self, b):
        self.apiQGis.setHiddenLayers(b)

    def canvasRefresh(self):
        self.apiQGis.canvasRefresh()

    def on(self, event, callback):
        self.apiQGis.on(event, callback)

    def off(self, event, callback):
        self.apiQGis.off(event, callback)

    def cleanProject(self):
        self.apiQGis.cleanProject()

    def getCurrentMapTool(self):
        self.apiQGis.getCurrentMapTool()

    def loadProcessingProvider(self, iconPath):
        self.apiQGis.loadProcessingProvider(iconPath)
    
    def unloadProcessingProvider(self):    
        self.apiQGis.unloadProcessingProvider()

    def runMapFunctions(self, functionList):
        return self.apiQGis.runMapFunctions(functionList)

    def activeTool(self, toolName, unsetTool=False):
        self.apiQGis.activeTool(toolName, unsetTool)

    def loadLayerActions(self, layerIds):
        self.apiQGis.loadLayerActions(layerIds)

    def pageRaster(self, direction):
        return self.apiQGis.pageRaster(direction)

    def createNewMapView(self):
        self.apiQGis.createNewMapView()

    def getDatabaseSettings(self):
        return self.apiQGis.getDatabaseSettings()
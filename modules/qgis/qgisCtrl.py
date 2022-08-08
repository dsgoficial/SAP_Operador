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

    def unload(self):
        self.apiQGis.unload()

    def load(self):
        self.apiQGis.load()

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
        return self.apiQGis.loadInputData(inputData)

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

    def setActionShortcut(self, actionName, shortcut):
        self.apiQGis.setActionShortcut(actionName, shortcut)

    def cleanDuplicateShortcut(self, actionName, shortcut):
        self.apiQGis.cleanDuplicateShortcut(actionName, shortcut)

    def addMenuBar(self, name):
        return self.apiQGis.addMenuBar(name)

    def addActionDigitizeToolBar(self, action):
        self.apiQGis.addActionDigitizeToolBar(action)

    def removeActionDigitizeToolBar(self, action):
        self.apiQGis.removeActionDigitizeToolBar(action)
    
    def createAction(self, name, iconPath, callback, checkable=False):
        return self.apiQGis.createAction(name, iconPath, callback, checkable)

    def deleteAction(self, action):
        self.apiQGis.deleteAction(action)

    def setHiddenLayers(self):
        self.apiQGis.setHiddenLayers()

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

    def createProgressMessageBar(self, title):
        return self.apiQGis.createProgressMessageBar(title)

    def removeMessageBar(self, messageBar):
        self.apiQGis.removeMessageBar(messageBar)

    def loadMapLayerStyles(self, loadedLayerIds, layerStyles, defaultStyle):
        self.apiQGis.loadMapLayerStyles(loadedLayerIds, layerStyles, defaultStyle)

    def changeMapLayerStyles(self, styleName):
        self.apiQGis.changeMapLayerStyles(styleName)

    def addWidgetToolBar(self, widget):
        return self.apiQGis.addWidgetToolBar(widget)

    def removeWidgetToolBar(self, widget):
        self.apiQGis.removeWidgetToolBar(widget)

    def addActionToolBar(self, action):
        return self.apiQGis.addActionToolBar(action)

    def removeActionToolBar(self, action):
        self.apiQGis.removeActionToolBar(action)

    def loadDefaultFieldValue(self, loadedLayerIds):
        self.apiQGis.loadDefaultFieldValue(loadedLayerIds)

    def zoomToFeature(self, layerId, layerSchema, layerName):
        self.apiQGis.zoomToFeature(layerId, layerSchema, layerName)

    def getLoadedVectorLayers(self):
        return self.apiQGis.getLoadedVectorLayers()

    def getActiveVectorLayer(self):
        return self.apiQGis.getActiveVectorLayer()

    def setPrimaryKeyReadOnly(self, layerIds, option):
        self.apiQGis.setPrimaryKeyReadOnly(layerIds, option)
    
    def startSelectRaster(self):
        self.apiQGis.startSelectRaster()

    def getQgisPluginsDirPath(self):
        return self.apiQGis.getQgisPluginsDirPath()

    def getPluginPaths(self):
        return self.apiQGis.getPluginPaths()

    def createMenuBar(self, menuName):
        return self.apiQGis.createMenuBar(menuName)

    def closeQgis(self):
        self.apiQGis.closeQgis()

    def getVisibleRasters(self):
        return self.apiQGis.getVisibleRasters()

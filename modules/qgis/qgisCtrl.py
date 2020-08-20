from Ferramentas_Producao.modules.qgis.interfaces.IQgisCtrl import IQgisCtrl
from Ferramentas_Producao.modules.qgis.factories.qgisApiSingleton import QgisApiSingleton
from Ferramentas_Producao.modules.qgis.factories.pluginsViewManagerSingleton import PluginsViewManagerSingleton
from qgis.utils import iface


class QgisCtrl(IQgisCtrl):

    def __init__(
            self,
            apiQGis=QgisApiSingleton.getInstance(),
            pluginViewQgis=PluginsViewManagerSingleton.getInstance()
        ):
        super(QgisCtrl, self).__init__()
        self.iface = iface
        self.apiQGis = apiQGis
        self.pluginViewQgis = pluginViewQgis

    def getMainWindow(self):
        return self.iface.mainWindow()

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
        self.pluginViewQgis.addDockWidget(dockWidget, side)

    def removeDockWidget(self, dockWidget):
        self.pluginViewQgis.removeDockWidget(dockWidget)
    
    def addActionDigitizeToolBar(self, action):
        self.pluginViewQgis.addActionDigitizeToolBar(action)
    
    def removeActionDigitizeToolBar(self, action):
        self.pluginViewQgis.removeActionDigitizeToolBar(action)

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
    
    def createAction(self, name, iconPath, shortcutKeyName, callback):
        return self.pluginViewQgis.createAction(name, iconPath, shortcutKeyName, callback)

    def deleteAction(self, action):
        self.pluginViewQgis.deleteAction(action)

    def setHiddenLayers(self, b):
        self.apiQGis.setHiddenLayers(b)

    def canvasRefresh(self):
        self.apiQGis.canvasRefresh()
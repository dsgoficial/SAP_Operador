from Ferramentas_Producao.modules.qgis.interfaces.IQgisApi import IQgisApi
from Ferramentas_Producao.modules.qgis.factories.inputDataFactory import InputDataFactory
from qgis.PyQt.QtXml import QDomDocument
from PyQt5 import QtCore, QtWidgets, QtGui 
from qgis import gui, core
import base64, os, processing
from qgis.utils import plugins, iface
from configparser import ConfigParser
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

class QgisApi(IQgisApi):

    def __init__(self,
            inputDataFactory=InputDataFactory()
        ):
       self.inputDataFactory = inputDataFactory

    def setProjectVariable(self, key, value):
        chiper_text = base64.b64encode(value.encode('utf-8'))
        core.QgsExpressionContextUtils.setProjectVariable(
            core.QgsProject().instance(), 
            key,
            chiper_text.decode('utf-8')
        )

    def getProjectVariable(self, key):
        current_project  = core.QgsProject().instance()
        chiper_text = core.QgsExpressionContextUtils.projectScope(current_project).variable(
            key
        )
        value = base64.b64decode(str.encode(chiper_text)).decode('utf-8') if chiper_text else ''
        return value

    def setSettingsVariable(self, key, value):
        qsettings = QtCore.QSettings()
        qsettings.setValue(key, value)

    def getSettingsVariable(self, key):
        qsettings = QtCore.QSettings()
        return qsettings.value(key)
    
    def hasModifiedLayers(self):
        for lyr in core.QgsProject.instance().mapLayers().values():
            if not(lyr.type() == core.QgsMapLayer.VectorLayer):
                continue
            if lyr.isModified():
                return True
        return False

    def getVersion(self):
        return core.QgsExpressionContextUtils.globalScope().variable('qgis_version').split('-')[0]

    def getPluginsVersions(self):
        pluginsVersions = []
        for name, plugin in plugins.items():
            try:
                metadata_path = os.path.join(
                    plugin.plugin_dir,
                    'metadata.txt'
                )
                with open(metadata_path) as mf:
                    cp = ConfigParser()
                    cp.readfp(mf)
                    pluginsVersions.append(
                        {
                            'nome' : name,
                            'versao' : cp.get('general', 'version').split('-')[0]
                        }
                    )
            except AttributeError:
                pass
        return pluginsVersions

    def createQgisAction(self, actionType, description, command):
        return core.QgsAction(actionType, description, command)

    def runProcessingModel(self, parametersData):
        doc = QDomDocument()
        doc.setContent(parametersData['model_xml'])
        model = core.QgsProcessingModelAlgorithm()
        model.loadVariant(core.QgsXmlUtils.readVariant( doc.firstChildElement() ))
        processing.runAndLoadResults(model, {})
        return "<p style=\"color:green\">{0}</p>".format('Rotina executada com sucesso!')

    def removeLayersWithouFeatures(self, layerIds):
        for layerId in layerIds:
            if not(layerId in core.QgsProject.instance().mapLayers().keys()):
                continue
            currentLyr = core.QgsProject.instance().mapLayers()[layerId]
            if len(currentLyr.allFeatureIds()) > 0:
                continue
            core.QgsProject.instance().removeMapLayer(currentLyr)

    def loadInputData(self, data):
        inputData = self.inputDataFactory.createInputDataType(
            data['tipo_insumo_id']
        )
        if not inputData:
            return
        inputData.load(data)

    def getLayerUriFromId(self, layerId):
        loadedLayers = core.QgsProject.instance().mapLayers()
        if not(layerId in loadedLayers):
            return
        return loadedLayers[layerId].dataProvider().uri().uri()
           

    def getLayerUriFromTable(self, layerSchema, layerName):
        layersUri = []
        loadedLayers = core.QgsProject.instance().mapLayers().values()
        for layer in loadedLayers:
            if not(
                    layer.dataProvider().uri().schema() == layerSchema
                    and
                    layer.dataProvider().uri().table() == layerName
                ):
                continue
            return layer.dataProvider().uri().uri()

    def setSettings(self, settings):
        for qgisVariable in settings:
            QtCore.QSettings().setValue(qgisVariable, settings[qgisVariable])
        
    def cleanShortcuts(self, settings):
        for qgisVariable in settings:
            if not('shortcuts' in qgisVariable):
                continue
            QtCore.QSettings().setValue(qgisVariable, '')

    def cleanActionShortcut(self, actionName):
        for a in gui.QgsGui.shortcutsManager().listActions():
            if not(actionName.lower() in a.objectName().lower()):
                continue
            a.setShortcut('')

    def setHiddenLayers(self, b):
        if b:
            iface.actionHideSelectedLayers().trigger()
        else:
            iface.actionShowSelectedLayers().trigger()

    def canvasRefresh(self):
        iface.mapCanvas().refresh()

    def getShortcutKey(self, shortcutKeyName):
        keys = {
            'Y': QtCore.Qt.Key_Y,
            'B': QtCore.Qt.Key_B,
        }
        if not shortcutKeyName in keys:
            return
        return keys[shortcutKeyName]

    def createAction(self, name, iconPath, shortcutKeyName, callback):
        a = QAction(
            QIcon(iconPath),
            name,
            iface.mainWindow()
        )
        if self.getShortcutKey(shortcutKeyName):
            a.setShortcut(self.getShortcutKey(shortcutKeyName))
        a.setCheckable(True)
        a.toggled.connect(callback)
        iface.digitizeToolBar().addAction(a)
        return a

    def deleteAction(self, action):
        iface.digitizeToolBar().removeAction(action)

    def addActionDigitizeToolBar(self, action):
        iface.digitizeToolBar().addAction(
            action
        )

    def removeActionDigitizeToolBar(self, action):
        iface.digitizeToolBar().removeAction(
            action
        )

    def addDockWidget(self, dockWidget, side):
        if side == 'right':
            iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)
        iface.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dockWidget)

    def removeDockWidget(self, dockWidget):
        if not dockWidget.isVisible():
            return
        iface.removeDockWidget(dockWidget)

    def on(self, event, callback):
        events = {
            'readProject': core.QgsProject.instance().readProject
        }
        events[event].connect(callback)

    def off(self, event, callback):
        events = {
            'readProject': core.QgsProject.instance().readProject
        }
        events[event].disconnect(callback)

    def cleanProject(self):
        core.QgsProject.instance().removeAllMapLayers()
        core.QgsProject.instance().layerTreeRoot().removeAllChildren()
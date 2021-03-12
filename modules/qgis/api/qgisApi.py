from Ferramentas_Producao.modules.qgis.interfaces.IQgisApi import IQgisApi
from Ferramentas_Producao.modules.qgis.factories.inputDataFactory import InputDataFactory
from Ferramentas_Producao.modules.qgis.factories.processingProviderFactory import ProcessingProviderFactory
from Ferramentas_Producao.modules.qgis.factories.layerActionsFactory import LayerActionsFactory
from Ferramentas_Producao.modules.qgis.factories.mapFunctionsFactory import MapFunctionsFactory
from Ferramentas_Producao.modules.qgis.factories.mapToolsFactory import MapToolsFactory

from qgis.PyQt.QtXml import QDomDocument
from PyQt5 import QtCore, QtWidgets, QtGui 
from qgis import gui, core
import base64, os, processing
from qgis.utils import plugins, iface
from configparser import ConfigParser
from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtGui import QIcon
import math
from configparser import ConfigParser


class QgisApi(IQgisApi):

    def __init__(self,
            inputDataFactory=InputDataFactory(),
            processingProviderFactory=ProcessingProviderFactory(),
            layerActionsFactory=LayerActionsFactory(),
            mapFunctionsFactory=MapFunctionsFactory(),
            mapToolsFactory=MapToolsFactory()
        ):
       self.inputDataFactory = inputDataFactory
       self.processingProviderFactory = processingProviderFactory
       self.mapFunctionsFactory = mapFunctionsFactory
       self.mapToolsFactory = mapToolsFactory
       self.layerActionsFactory = layerActionsFactory

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
        inputData = self.inputDataFactory.createInputDataType( data['tipo_insumo_id'] )
        if not inputData:
            return
        return inputData.load(data)

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

    def setActionShortcut(self, objectName):
        pass
        #selector = QgsGui.shortcutsManager().listAll()[175]
        #QgsGui.shortcutsManager().setObjectKeySequence(selector, 'S')

    def addMenuBar(self, name):
        menu = QMenu(iface.mainWindow())
        menu.setObjectName(name)
        menu.setTitle(name)
        iface.mainWindow().menuBar().insertMenu(iface.firstRightStandardMenu().menuAction(), menu)
        return menu

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

    def createAction(self, name, iconPath, callback, shortcutKeyName, checkable):
        a = QAction(
            QIcon(iconPath),
            name,
            iface.mainWindow()
        )
        if self.getShortcutKey(shortcutKeyName):
            a.setShortcut(self.getShortcutKey(shortcutKeyName))
        a.setCheckable(checkable)
        a.triggered.connect(callback)
        return a

    def addActionDigitizeToolBar(self, action):
        iface.digitizeToolBar().addAction(action)

    def removeActionDigitizeToolBar(self, action):
        iface.digitizeToolBar().removeAction(action)

    def addDockWidget(self, dockWidget, side):
        if side == 'right':
            iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)
        iface.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dockWidget)

    def removeDockWidget(self, dockWidget):
        if not dockWidget.isVisible():
            return
        iface.removeDockWidget(dockWidget)
    
    def getEvents(self):
        return {
            'readProject': core.QgsProject.instance().readProject,
            'SaveAllEdits': iface.actionSaveAllEdits().triggered,
            'SaveActiveLayerEdits': iface.actionSaveActiveLayerEdits().triggered,
        }

    def on(self, event, callback):
        self.getEvents()[event].connect(callback)

    def off(self, event, callback):
        self.getEvents()[event].disconnect(callback)

    def cleanProject(self):
        core.QgsProject.instance().removeAllMapLayers()
        core.QgsProject.instance().layerTreeRoot().removeAllChildren()

    def getCurrentMapTool(self):
        return iface.mapCanvas().mapTool()

    def loadProcessingProvider(self, iconPath):
        fpProcProvider = self.processingProviderFactory.createProvider('fp')
        fpProcProvider.setIconPath(iconPath)
        core.QgsApplication.processingRegistry().addProvider(fpProcProvider)
    
    def unloadProcessingProvider(self):    
        fpProcProvider = self.processingProviderFactory.createProvider('fp')
        core.QgsApplication.processingRegistry().removeProvider(fpProcProvider)

    def runMapFunctions(self, functionList):
        for functionData in functionList:
            mapFunction = self.mapFunctionsFactory.getFunction(functionData['name'])
            result = mapFunction.run(iface.activeLayer())
            if result[0]:
                continue
            return result
        return result

    def activeTool(self, toolName, unsetTool=False):
        tool = self.mapToolsFactory.getTool(toolName)
        if unsetTool:
            iface.mapCanvas().unsetMapTool(tool)
        else:
            iface.mapCanvas().setMapTool(tool)

    def pageRaster(self, direction):
        groupName = 'imagens_dinamicas'
        root = core.QgsProject.instance().layerTreeRoot()
        grupo = root.findGroup(groupName)
        if not grupo:
            return (False, 'Crie um grupo com o nome "{0}" e coloque as camadas do tipo "Raster" para paginação.'.format(groupName))
        images = [
            tLayer for tLayer in grupo.findLayers() 
            if tLayer.layer().type() == core.QgsMapLayer.RasterLayer
        ]
        if len(images) == 0:
            return (False, 'O grupo "{0}" não possue camadas do tipo "Raster"'.format(groupName))
        visibleImages = [ tLayer for tLayer in images if tLayer.isVisible() ]
        if len(visibleImages) == 0 or len(visibleImages) > 1:
            [ tLayer.setVisible(False) for tLayer in visibleImages]             
            images[0].setVisible(True)
            return
        
        def pageDown(currentPostion, images):
            return 0 if currentPostion == (len(images)-1) else (currentPostion + 1)
        def pageUp(currentPostion, images):
            return (len(images)-1) if currentPostion == 0 else (currentPostion - 1)
        pageFunctions = {
            'down': pageDown,
            'up': pageUp
        }
        if not(direction in pageFunctions):
            return (False, 'Direção inválida')
        currentPostion = images.index(rastersVisiveis[0])
        nextPosition = pageFunctions[direction](currentPostion, images)
        images[currentPostion].setVisible(False)
        images[nextPosition].setVisible(True)

    def createNewMapView(self):
        createNewMapView = self.mapFunctionsFactory.getFunction('CreateNewMapView')
        createNewMapView.run()
        
    def loadLayerActions(self, layerIds):
        actions = {
            'Mostrar feição': self.layerActionsFactory.createAction('FlashFeature'),   
        }
        layers = core.QgsProject.instance().mapLayers()
        for layerId in layers:
            if not(layerId in layerIds):
                continue
            for name in actions:
                customAction = gui.QgsMapLayerAction( name , iface, layers[layerId])
                gui.QgsGui.mapLayerActionRegistry().addMapLayerAction(customAction)
                customAction.triggeredForFeature.connect(actions[name].execute)

    def getMainWindow(self):
        return iface.mainWindow()
        
    def updateMainWindow(self, customizationData):
        mSettings = core.QSettings()
        mw = iface.mainWindow()
        cp = ConfigParser()
        cp.read_string(customizationData)
        items = list(cp['Customization'].items())

        menuBar = mw.menuBar()
        menuCustomization = [ item for item in items if itemm[0].startswith('menus') ]
        
        mSettings.beginGroup( "Customization/Menus" )
        menus = menuBar.findChildren(core.QMenu)
        for menu in menus:
            if not menu.objectName() or not(menu.objectName() in customLayout):
                continue
            visible = customLayout[menu.objectName()]
            if not visible :
                menuBar.removeAction( menu.menuAction() )
            else:
                menuBar.addAction( menu.menuAction() )
        mSettings.endGroup()

        mSettings.beginGroup( "Customization/Toolbars" )
        toolBars = mw.findChildren(core.QToolBar)
        for toolBar in toolBars:
            objectName = toolBar.objectName()
            if not objectName or not(objectName in customLayout):
                continue
            visible = customLayout[objectName]
            if not visible :
                mw.removeToolBar( toolBar )
                iface.viewMenu().removeAction(toolBar.toggleViewAction())
            else:
                iface.viewMenu().addAction(toolBar.toggleViewAction())
                toolBar.toggleViewAction().trigger() if not toolBar.isVisible() else ''
        mSettings.endGroup()

        mSettings.beginGroup( "Customization/Docks" )
        docks = mw.findChildren(core.QDockWidget)
        for dock in docks:
            objectName = dock.objectName()
            if not objectName or not(objectName in customLayout):
                continue
            visible = customLayout[objectName]
            if not visible :
                mw.removeDockWidget( dock )
        mSettings.endGroup()

    def getDatabaseSettings(self):
        dbaliases = sorted([ 
            key.split('/')[2] 
            for key in QtCore.QSettings().allKeys() 
            if 'postgresql' in key.lower() 
                and 
                'host' in key.lower() 
                and 
                len(key.split('/')) > 3
        ])
        dbsettings = []
        for dbalias in dbaliases:
            if not self.isValidDatabaseSettings(dbalias):
                continue
            dbsettings.append({
                'alias': dbalias,
                'database':QtCore.QSettings().value('PostgreSQL/connections/'+dbalias+'/database'),
                'host':QtCore.QSettings().value('PostgreSQL/connections/'+dbalias+'/host'),
                'port':QtCore.QSettings().value('PostgreSQL/connections/'+dbalias+'/port'),
                'username':QtCore.QSettings().value('PostgreSQL/connections/'+dbalias+'/username'),
                'password':QtCore.QSettings().value('PostgreSQL/connections/'+dbalias+'/password'),
            })
        return dbsettings

    def isValidDatabaseSettings(self, dbalias):
        return (
            QtCore.QSettings().value('PostgreSQL/connections/'+dbalias+'/savePassword') == 'true'
            and
            QtCore.QSettings().value('PostgreSQL/connections/'+dbalias+'/saveUsername') == 'true'
        )


    def createProgressMessageBar(self, title):
        progressMessageBar = iface.messageBar().createMessage('Ferramentas de Produção', title)
        progress = QtWidgets.QProgressBar()
        progress.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        iface.messageBar().pushWidget(progressMessageBar, core.Qgis.Info)
        return progressMessageBar, progress

    def removeMessageBar(self, messageBar):
        iface.messageBar().popWidget(messageBar)










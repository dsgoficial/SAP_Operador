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
import math, uuid
from configparser import ConfigParser
import subprocess
import platform
import shutil
import json

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
        self.customToolBar = None
    
    def load(self):
        self.customToolBar = iface.addToolBar('FPTools')

    def unload(self):
        self.unloadProcessingProvider()
        del self.customToolBar

    def unloadProcessingProvider(self):    
        fpProcProvider = self.processingProviderFactory.createProvider('fp')
        core.QgsApplication.processingRegistry().removeProvider(fpProcProvider)

    def addWidgetToolBar(self, widget):
        return self.customToolBar.addWidget(widget)

    def addActionToolBar(self, action):
        self.customToolBar.addAction(action)

    def removeActionToolBar(self, action):
        self.customToolBar.removeAction(action)
    
    def setProjectVariable(self, key, value, encrypt=True):
        if not encrypt:
            core.QgsExpressionContextUtils.setProjectVariable(
                core.QgsProject().instance(), 
                key,
                value
            )
            return
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

    def checkModifiedLayersByStepId(self, stepId, noteLayers):
        if stepId == 3: #correcao
            for noteLayer in noteLayers:
                layer = self.getLayerFromTable(
                    noteLayer['schema'],
                    noteLayer['nome']
                )
                if not layer:
                    raise Exception("Carregue as camadas de apontamento!")
                for feature in layer.getFeatures():
                    if (
                        feature[noteLayer['atributo_situacao_correcao']] == 1
                        or
                        (
                            feature[noteLayer['atributo_situacao_correcao']] != 1
                            and
                            feature[noteLayer['atributo_justificativa_apontamento']] != None
                        )
                    ):
                        continue
                    return False
        elif stepId == 2: #revisao
            for noteLayer in noteLayers:
                layer = self.getLayerFromTable(
                    noteLayer['nome'],
                    noteLayer['schema']
                )
                if not layer:
                    raise Exception("Carregue as camadas de apontamento!")
                if len(list(layer.getFeatures())) == 0:
                    continue
                return False
        return True

    def runProcessingModel(self, parametersData):
        self.setActiveGroup("SAIDA_MODEL")
        doc = QDomDocument()
        doc.setContent(parametersData['model_xml'])
        model = core.QgsProcessingModelAlgorithm()
        model.loadVariant(core.QgsXmlUtils.readVariant( doc.firstChildElement() ))
        parameters = json.loads(parametersData['parametros']) if parametersData['parametros'] else {}
        processing.runAndLoadResults(model, parameters)
        return "<p style=\"color:green\">{0}</p>".format('Rotina executada com sucesso!')

    def setActiveGroup(self, groupName, pos=0):
        iface.mapCanvas().freeze(True)
        rootNode = core.QgsProject.instance().layerTreeRoot()
        group = rootNode.findGroup(groupName)
        if group is None:
            group = rootNode.insertGroup(pos, groupName)
        view = iface.layerTreeView()
        m = view.model()
        listIndexes = m.match(m.index(0, 0), QtCore.Qt.DisplayRole, groupName, QtCore.Qt.MatchFixedString)
        if listIndexes:
            i = listIndexes[0]
            view.selectionModel().setCurrentIndex(i, QtCore.QItemSelectionModel.ClearAndSelect)
        iface.mapCanvas().freeze(False)

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

    def getLayerFromTable(self, layerSchema, layerName):
        loadedLayers = core.QgsProject.instance().mapLayers().values()
        for layer in loadedLayers:
            if not(
                    layer.dataProvider().uri().schema() == layerSchema
                    and
                    layer.dataProvider().uri().table() == layerName
                ):
                continue
            return layer

    def getLayerFromName(self, layerName):
        loadedLayers = core.QgsProject.instance().mapLayers().values()
        for layer in loadedLayers:
            if not(
                    layer.dataProvider().uri().table() == layerName
                ):
                continue
            return layer

    def addMenuBar(self, name):
        menu = QMenu(iface.mainWindow())
        menu.setObjectName(name)
        menu.setTitle(name)
        iface.mainWindow().menuBar().insertMenu(iface.firstRightStandardMenu().menuAction(), menu)
        return menu

    def setHiddenLayers(self):
        layerTreeRoot = core.QgsProject.instance().layerTreeRoot()
        f = iface.activeLayer()
        if f:
            b = layerTreeRoot.findLayer(f.id()).isVisible()
            if b:
                iface.actionHideSelectedLayers().trigger()
            else:
                iface.actionShowSelectedLayers().trigger()
            return
        selectedGroups = iface.layerTreeView().selectedNodes()
        if not(len(selectedGroups) == 1):
            return
        group = selectedGroups[0]
        group.setItemVisibilityChecked(
            not group.itemVisibilityChecked()
        )

    def getShortcutKey(self, shortcutKeyName):
        keys = {
            'Y': QtCore.Qt.Key_Y,
            'B': QtCore.Qt.Key_B,
        }
        if not shortcutKeyName in keys:
            return
        return keys[shortcutKeyName]

    def createAction(self, name, iconPath, callback, shortcutKeyName='', register=False):
        a = QAction(
            QIcon(iconPath),
            name,
            iface.mainWindow()
        )
        if self.getShortcutKey(shortcutKeyName):
            a.setShortcut(self.getShortcutKey(shortcutKeyName))
        a.triggered.connect(callback)
        if register:
            gui.QgsGui.shortcutsManager().registerAction(a)
        return a

    def addActionDigitizeToolBar(self, action):
        iface.digitizeToolBar().addAction(action)

    def addDockWidget(self, dockWidget, side):
        position = QtCore.Qt.RightDockWidgetArea if side == 'right' else QtCore.Qt.LeftDockWidgetArea
        dockers = iface.mainWindow().findChildren(QtWidgets.QDockWidget)
        tabify = [ d.objectName() for d in dockers ]
        iface.addTabifiedDockWidget(position, dockWidget, tabify, True)

    def removeDockWidget(self, dockWidget):
        if not dockWidget.isVisible():
            return
        iface.removeDockWidget(dockWidget)

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

    def changeMapLayerStyles(self, styleName):
        for layer in core.QgsProject.instance().mapLayers().values():
            #lyr.styleManager().styles()
            layer.styleManager().setCurrentStyle(styleName)

    def loadMapLayerStyles(self, loadedLayerIds, layerStyles, defaultStyle):
        for layerId in loadedLayerIds:
            layer = core.QgsProject.instance().mapLayers()[layerId]
            layerName = layer.dataProvider().uri().table()
            layerSettings = [ item for item in layerStyles if item['layerName'] == layerName ]
            if not layerSettings:
                continue
            for style in layerSettings[0]['styles']:
                """ mapLayerStyle = core.QgsMapLayerStyle(style['qml'])
                layer.styleManager().addStyle(style['name'], mapLayerStyle) """
                doc = QDomDocument()
                doc.setContent(style['qml'])
                layer.importNamedStyle(doc, core.QgsMapLayer.Symbology | core.QgsMapLayer.Labeling )
                layer.styleManager().addStyleFromLayer(style['name'])
            layer.styleManager().removeStyle('default')
            layer.styleManager().setCurrentStyle(defaultStyle)

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

    def getLayerFromIds(self, layerIds):
        loadedLayers = core.QgsProject.instance().mapLayers()
        return [
            loadedLayers[layerId]
            for layerId in layerIds
            if layerId in loadedLayers
        ]
            
    def setSettings(self, settings):
        for qgisVariable in settings:
            QtCore.QSettings().setValue(qgisVariable, settings[qgisVariable])
        
    def cleanShortcuts(self, settings):
        for qgisVariable in settings:
            if not('shortcuts' in qgisVariable):
                continue
            QtCore.QSettings().setValue(qgisVariable, '')

    def cleanDuplicateShortcut(self, actionName, shortcut):
        for a in gui.QgsGui.shortcutsManager().listActions():
            if not( shortcut.lower() == a.shortcut().toString().lower() ):
                continue
            a.setShortcut('')
            gui.QgsGui.shortcutsManager().setObjectKeySequence(a, '')

    def setActionShortcut(self, actionName, shortcut):
        for a in gui.QgsGui.shortcutsManager().listActions():
            if not(actionName.lower() == a.text().lower().replace('&','')):
                continue
            a.setShortcut(shortcut)
            gui.QgsGui.shortcutsManager().setObjectKeySequence(a, shortcut)

    def canvasRefresh(self):
        iface.mapCanvas().refresh()

    def removeActionDigitizeToolBar(self, action):
        iface.digitizeToolBar().removeAction(action)

    def getEvents(self):
        return {
            'ReadProject': core.QgsProject.instance().readProject,
            'SaveAllEdits': iface.actionSaveAllEdits().triggered,
            'SaveActiveLayerEdits': iface.actionSaveActiveLayerEdits().triggered,
            'MessageLog': core.QgsApplication.messageLog().messageReceived,
            'LayersAdded': core.QgsProject.instance().layersAdded,
            'NewProject': iface.newProjectCreated,
        }

    def on(self, event, callback):
        self.getEvents()[event].connect(callback)
        return True

    def off(self, event, callback):
        try:
            self.getEvents()[event].disconnect(callback)
            return True
        except:
            return False

    def cleanProject(self):
        core.QgsProject.instance().removeAllMapLayers()
        core.QgsProject.instance().layerTreeRoot().removeAllChildren()
        self.canvasRefresh()

    def getCurrentMapTool(self):
        return iface.mapCanvas().mapTool()

    def loadProcessingProvider(self, iconPath):
        pass
        """ fpProcProvider = self.processingProviderFactory.createProvider('fp')
        fpProcProvider.setIconPath(iconPath)
        core.QgsApplication.processingRegistry().addProvider(fpProcProvider) """

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
        return tool

    def getVisibleRasters(self):
        root = core.QgsProject.instance().layerTreeRoot()
        return [
            tl.layer()
            for tl in root.findLayers()
            if tl.isVisible() and tl.layer().type() == core.QgsMapLayer.RasterLayer
        ]

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

    def setPrimaryKeyReadOnly(self, layerIds, option):
        layers = core.QgsProject.instance().mapLayers()
        for layerId in layers:
            if not(layerId in layerIds):
                continue
            layer = layers[layerId]
            editFormConfig = layer.editFormConfig()
            for fieldIdx in layer.primaryKeyAttributes():
                editFormConfig.setReadOnly(fieldIdx, option)
            layer.setEditFormConfig(editFormConfig)

    def setFieldsReadOnly(self, layerIds, fields, option):
        layers = core.QgsProject.instance().mapLayers()
        for layerId in layers:
            if not(layerId in layerIds):
                continue
            layer = layers[layerId]
            editFormConfig = layer.editFormConfig()
            for fieldName in fields:
                fieldIdx = layer.fields().indexOf(fieldName)
                if fieldIdx < 0:
                    continue
                editFormConfig.setReadOnly(fieldIdx, option)
            layer.setEditFormConfig(editFormConfig)

    def getMainWindow(self):
        return iface.mainWindow()

    def enableNMEA(self):
        docks = iface.mainWindow().findChildren(QtWidgets.QDockWidget)
        GPSInformation = next(filter(lambda o: o.objectName() == 'GPSInformation', docks) , None)
        if not GPSInformation:
            return
        buttons = GPSInformation.findChildren(QtWidgets.QPushButton)
        mBtnLogFile = next(filter(lambda o: o.objectName() == 'mBtnLogFile', buttons) , None)
        if not mBtnLogFile:
            return
        mBtnLogFile.setEnabled(True)
        
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

    def loadDefaultFieldValue(self, layerIds, fields):
        layers = core.QgsProject.instance().mapLayers()
        for layerId in layers:
            if not(layerId in layerIds):
                continue
            layer = layers[layerId]

            for field in fields:
                fieldIdx = layer.fields().indexOf(field['name'])
                valueDefinition = layer.defaultValueDefinition(fieldIdx)
                valueDefinition.setApplyOnUpdate(True)
                valueDefinition.setExpression('{}'.format(field['value']))
                layer.setDefaultValueDefinition(fieldIdx, valueDefinition)
    
    def zoomToFeature(self, layerId, layerSchema, layerName):
        loadedLayers = core.QgsProject.instance().mapLayers().values()
        for layer in loadedLayers:
            if not(
                    layer.dataProvider().uri().schema() == layerSchema
                    and
                    layer.dataProvider().uri().table() == layerName
                ):
                continue
            layer.select(int(layerId))
            iface.actionZoomToSelected().trigger()
            break

    def getLoadedVectorLayers(self):
        return [
            l
            for l in core.QgsProject.instance().mapLayers().values()
            if l.type() == core.QgsMapLayer.VectorLayer
        ]
    
    def getActiveVectorLayer(self):
        activeLayer = iface.activeLayer()
        if not( activeLayer and activeLayer.type() == core.QgsMapLayer.VectorLayer ):
            return
        return activeLayer

    def startSelectRaster(self):
        selectRaster = self.mapFunctionsFactory.getFunction('SelectRaster')
        selectRaster.run()

    def getQgisPluginsDirPath(self):
        settingsPath = core.QgsApplication.qgisSettingsDirPath()
        if platform.system().lower() == 'windows':
            settingsPath = settingsPath.replace('/', '\\')
        return os.path.join(
            settingsPath,
            'python',
            'plugins'
        )

    def getPluginPaths(self):
        if platform.system().lower() == 'windows':
            return self.getWindowsPluginPaths()
        else:
            return self.getLinuxPluginPaths()

    def getWindowsPluginPaths(self):
        repositoryPluginsPath = self.getQgisPluginsDirPath()
        p = subprocess.Popen(
            'cmd /u /c "dir {0} /B"'.format(repositoryPluginsPath), 
            stdout=subprocess.PIPE, 
            shell=True
        )
        result = p.communicate()
        return [
            (name, os.path.join(repositoryPluginsPath, name))
            for name in result[0].decode('u16').split('\r\n')
        ]

    def getLinuxPluginPaths(self):
        repositoryPluginsPath = self.getQgisPluginsDirPath()
        p = subprocess.Popen(
            'ls {0}'.format(repositoryPluginsPath), 
            stdout=subprocess.PIPE, 
            shell=True
        )
        result = p.communicate()
        return [
            (name, os.path.join(repositoryPluginsPath, name))
            for name in result[0].decode('u8').split('\n')
        ]

    def createMenuBar(self, menuName):
        menu = QtWidgets.QMenu(iface.mainWindow())
        menu.setObjectName(menuName)
        menu.setTitle(menuName)
        iface.mainWindow().menuBar().insertMenu(
            iface.firstRightStandardMenu().menuAction(), 
            menu
        )
        return menu

    def closeQgis(self):
        core.QgsApplication.taskManager().cancelAll()
        iface.actionExit().trigger()

    def setActiveLayerByName(self, layerName):
        layer = self.getLayerFromName(layerName)
        if not layer:
            return
        iface.setActiveLayer(layer)

    def loadThemes(self, themes):
        for theme in themes:
            themeLayers = [ '{}.{}'.format(l['schema'], l['camada']) for l in theme['camadas'] ]
            root = core.QgsProject().instance().layerTreeRoot().clone()
            for rLayer in root.findLayers():
                rLayer.setItemVisibilityChecked(False)
                rLayerName = '{}.{}'.format(
                    rLayer.layer().dataProvider().uri().schema(),
                    rLayer.layer().dataProvider().uri().table()
                )
                if not(rLayerName in themeLayers):
                    continue
                rLayer.setItemVisibilityChecked(True)
            model = core.QgsLayerTreeModel(root)
            themeCollection = core.QgsProject.instance().mapThemeCollection()
            themeCollection.insert(theme['nome'], core.QgsMapThemeCollection.createThemeFromCurrentState(root, model))



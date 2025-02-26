from SAP_Operador.factories.GUIFactory import GUIFactory
from SAP_Operador.factories.timerFactory import TimerFactory
from SAP_Operador.controllers.prodToolsCtrl import ProdToolsCtrl
from SAP_Operador.modules.combinationViewer.controllers.combinationViewerCtrl import CombinationViewerCtrl
from SAP_Operador.modules.rasterMetadata.controllers.rasterMetadataCtrl import RasterMetadataCtrl
import os
from PyQt5.QtCore import QThread, pyqtSignal

class ProdToolsSettingsCtrl(ProdToolsCtrl):

    reclassifyMode = pyqtSignal()
    
    def __init__(
            self,
            qgis,
            pluginUpdater,
            timerFactory=None,
            combinationViewer=None,
            rasterMetadata=None,
        ):
        super(ProdToolsSettingsCtrl, self).__init__()
        self.qgis = qgis
        self.pluginUpdater = pluginUpdater
        self.timerFactory = TimerFactory() if timerFactory is None else timerFactory
        self.combinationViewer = CombinationViewerCtrl() if combinationViewer is None else combinationViewer
        self.rasterMetadata = RasterMetadataCtrl() if rasterMetadata is None else rasterMetadata
        self.saveTimer = None
        self.showMarkers = True
        self.menuBarActions = []

    def load(self):
        self.loadCustomQgisSettings()
        self.createActionsMenuBar()
        self.createMenuBar()

    def unload(self):
        for action in self.getMenuBarActions():
            self.menuBarMain.removeAction(action)
        self.setMenuBarActions([])
        self.menuBarMain.deleteLater()

    def createActionsMenuBar(self):
        menuBarActions = []
        actions = self.getMenuBarActionSettings() + self.pluginUpdater.getUpdaterActions()
        for actionConfig in actions:
            action = self.qgis.createAction(
                actionConfig['name'],
                actionConfig['iconPath'],
                actionConfig['callback']
            )
            menuBarActions.append(action)
        self.setMenuBarActions(menuBarActions)

    def setMenuBarActions(self, menuBarActions):
        self.menuBarActions = menuBarActions

    def getMenuBarActions(self):
        return self.menuBarActions

    def createMenuBar(self):
        self.menuBarMain = self.qgis.addMenuBar('SAP Operador')
        for action in self.getMenuBarActions():
            self.menuBarMain.addAction(action)

    def addActionMenu(self, action):
        self.menuBarMain.addAction(action)

    def initSaveTimer(self):
        if self.saveTimer:
            self.saveTimer.reset()
            return
        self.saveTimer = self.timerFactory.createTimer('Timer')
        self.saveTimer.addCallback(self.saveMessage)
        self.saveTimer.start(1000*60*10)
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
        #self.qgis.setActionShortcut('EnableSnappingAction', '')

    def showMarkersOnlySelectedFeatures(self):
        values = {
            True: 'true',
            False: 'false'
        }
        self.qgis.setSettings({
            'digitizing/marker-only-for-selected': values[self.showMarkers]
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

    def checkPluginUpdates(self):
        return self.pluginUpdater.checkUpdates()
    
    def getMenuBarActionSettings(self):
        iconRootPath = os.path.join(
                os.path.dirname(__file__),
                '..',
                'icons'
        )
        return [
            {
                'name': 'Suavizador de linhas',
                'iconPath':os.path.join(iconRootPath, 'smoothLayer.png'),
                'callback': self.smoothLine
            },
            {
                'name': 'Fechar linha',
                'iconPath':os.path.join(iconRootPath, 'closeLine.png'),
                'callback': self.closeLine
            },
            {
                'name': 'Criar nova visualização de mapa',
                'iconPath':os.path.join(iconRootPath, 'newmapview.png'),
                'callback': lambda: self.qgis.createNewMapView()
            },
            {
                'name': 'Convergir vertices de feições',
                'iconPath':os.path.join(iconRootPath, 'convergencepoint.png'),
                'callback': lambda: self.qgis.activeTool('ConvergencePoint')
            },
            {
                'name': 'Visualizado de combinações',
                'iconPath':os.path.join(iconRootPath, 'combinationViewer.svg'),
                'callback': lambda: self.combinationViewer.openDialog()
            },
            {
                'name': 'Raster Metadata Atribute',
                'iconPath':os.path.join(iconRootPath, 'raster.png'),
                'callback': lambda: self.rasterMetadata.openDialog()
            },
            {
                'name': 'Habilitar NMEA',
                'iconPath':os.path.join(iconRootPath, 'nmea.png'),
                'callback': self.qgis.enableNMEA
            },
            # {
            #     'name': 'Reclassify Mode',
            #     'iconPath': '',
            #     'callback': self.reclassifyMode.emit
            # },
        ]

        
        """ {
            'name': 'Aparar linha',
            'iconPath':os.path.join(iconRootPath, 'trim.png'),
            'callback': lambda: self.qgis.activeTool('TrimLineMapTool')
        },
        {
            'name': 'Expandir linha',
            'iconPath':os.path.join(iconRootPath, 'expand.png'),
            'callback': lambda: self.qgis.activeTool('ExpandLineMapTool')
        } """

    def getCustomQgisSettings(self):
        return {
            u'qgis/parallel_rendering' : u'true',
            u'qgis/max_threads' : 8,
            u'qgis/simplifyDrawingHints': u'0',            
            u'qgis/digitizing/marker_only_for_selected' : u'false',
            'qgis/digitizing/default_snapping_tolerance' : '10',
            'qgis/digitizing/default_snap_enabled' : 'true', 
            u'qgis/digitizing/default_snap_type' : u'Vertex',
            'Map/scales' : '1:2217000,1:740000,1:370000,1:250000,1:185000,1:100000,1:50000,1:25000,1:10000,1:5000,1:2000,1:1000,1:500,1:250',
            'qgis/digitizing/line_width' : '3',
            'qgis/digitizing/line_color_alpha' : '63',
            'qgis/digitizing/fill_color_alpha' : '40',
            u'qgis/default_selection_color_alpha': u'63',
            "/qgis/legendsymbolMaximumSize": '5.0'
        }

    
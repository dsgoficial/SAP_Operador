from Ferramentas_Producao.factories.GUIFactory import GUIFactory
from Ferramentas_Producao.factories.timerFactory import TimerFactory
from Ferramentas_Producao.controllers.prodToolsCtrl import ProdToolsCtrl

import os

class ProdToolsSettingsCtrl(ProdToolsCtrl):
    
    def __init__(
            self,
            qgis,
            timerFactory=TimerFactory()
        ):
        super(ProdToolsSettingsCtrl, self).__init__()
        self.qgis = qgis
        self.timerFactory = timerFactory
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
        for actionConfig in self.getMenuBarActionSettings():
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
        self.menuBarMain = self.qgis.addMenuBar('Ferramentas de Produção')
        for action in self.getMenuBarActions():
            self.menuBarMain.addAction(action)

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
        self.qgis.setActionShortcut('EnableSnappingAction', '')

    def onOffLayers(self):
        self.qgis.setHiddenLayers()

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
                '..',
                'icons'
        )
        return [
            {
                'name': 'Ligar/Desligar camada',
                'iconPath':os.path.join(iconRootPath, 'on_off.png'),
                'callback': self.onOffLayers
            },
            {
                'name': 'Mostrar/Esconder marcadores para feições selecionadas',
                'iconPath':os.path.join(iconRootPath, 'vertex.png'),
                'callback': self.showMarkersOnlySelectedFeatures
            },
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
                'name': 'Aparar linha',
                'iconPath':os.path.join(iconRootPath, 'trim.png'),
                'callback': lambda: self.qgis.activeTool('TrimLineMapTool')
            },
            {
                'name': 'Expandir linha',
                'iconPath':os.path.join(iconRootPath, 'expand.png'),
                'callback': lambda: self.qgis.activeTool('ExpandLineMapTool')
            },
            {
                'name': 'Paginar raster para cima',
                'iconPath':os.path.join(iconRootPath, 'pageup.png'),
                'callback': lambda direction='up': self.pageRaster(direction)
            },
            {
                'name': 'Paginar raster para baixo',
                'iconPath':os.path.join(iconRootPath, 'pagedown.png'),
                'callback': lambda direction='down': self.pageRaster(direction)
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
            }
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
            u'qgis/default_selection_color_alpha': u'63'
        }

    def loadCustomQgisShortcuts(self):
        for setting in self.getShortcutsQgis():
            self.qgis.updateShortcut(
                setting['descricao'],
                setting['shorcut'],
            )

    def getShortcutsQgis(self):
        return [
            {
                'shorcut': 'Z',
                'descricao': 'Sair do QGIS'
            },
            {
                'shorcut': 'Z',
                'descricao': 'Exit QGIS'
            }
        ]

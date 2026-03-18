import os, sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


from .controllers.loginCtrl import LoginCtrl
from .controllers.remoteProdToolsDockCtrl import RemoteProdToolsDockCtrl
from .controllers.localProdToolsDockCtrl import LocalProdToolsDockCtrl
from .controllers.prodToolsSettingsCtrl import ProdToolsSettingsCtrl

from .modules.sap.controllers.remoteSapCtrl import RemoteSapCtrl
from .modules.sap.controllers.localSapCtrl import LocalSapCtrl
from .modules.qgis.scripts.toggle import toggle
from .modules.pluginUpdater.controllers.updaterCtrl import UpdaterCtrl

from .modules.qgis.qgisApi import QgisApi
from .modules.fme.factories.fmeApiSingleton import FmeApiSingleton
from .modules.utils.factories.utilsFactory import UtilsFactory
from .modules.dsgTools.factories.processingQgisFactory import ProcessingQgisFactory
from .modules.dsgTools.factories.toolFactory import ToolFactory
from .modules.database.factories.databaseFactory import DatabaseFactory
from .modules.pomodoro.pomodoro import Pomodoro
from .config import Config
from qgis.utils import iface

class Main:

    def __init__(self, iface):    
        super(Main, self).__init__()
        self.plugin_dir = os.path.dirname(__file__)
        self.qgisCtrl = QgisApi()
        self.externalInstance = None
        
        remoteSap = RemoteSapCtrl( self.qgisCtrl )
        self.updaterCtrl = UpdaterCtrl( remoteSap, self.qgisCtrl )
        self.prodToolsSettingsCtrl = ProdToolsSettingsCtrl( 
            self.qgisCtrl,
            self.updaterCtrl 
        )
        self.remoteProdToolsDockCtrl = RemoteProdToolsDockCtrl(
            sap=remoteSap,
            qgis=self.qgisCtrl,
            databaseFactory=DatabaseFactory(),
            processingFactoryDsgTools=ProcessingQgisFactory(),
            fme=FmeApiSingleton.getInstance(),
            prodToolsSettings=self.prodToolsSettingsCtrl,
            toolFactoryDsgTools=ToolFactory()
        )
        self.localProdToolsDockCtrl = LocalProdToolsDockCtrl(
            sap=LocalSapCtrl( self.qgisCtrl ),
            qgis=self.qgisCtrl,
            databaseFactory=DatabaseFactory(),
            processingFactoryDsgTools=ProcessingQgisFactory(),
            fme=FmeApiSingleton.getInstance(),
            prodToolsSettings=self.prodToolsSettingsCtrl,
            toolFactoryDsgTools=ToolFactory()
        )
        self.loginCtrl = LoginCtrl(
            qgis=self.qgisCtrl,
            remoteProdToolsDockCtrl=self.remoteProdToolsDockCtrl,
            localProdToolsDockCtrl=self.localProdToolsDockCtrl
        )
        self.toggle_buffer_pressed = False
        self.toggle_vertices_pressed = False
    
    def getPluginIconPath(self):
        return os.path.join(
            os.path.abspath(os.path.join(
                os.path.dirname(__file__)
            )),
            'icons',
            'production.png'
        )
    
    def getToggleBufferIconPath(self):
        return os.path.join(
            os.path.abspath(os.path.join(
                os.path.dirname(__file__)
            )),
            'icons',
            'buffer_toggle.svg'
        )
    def getToggleVerticesIconPath(self):
        return os.path.join(
            os.path.abspath(os.path.join(
                os.path.dirname(__file__)
            )),
            'icons',
            'vertices_toggle.svg'
        )

    def initGui(self):
        self.qgisCtrl.load()
        self.prodToolsSettingsCtrl.load()
        self.widget = self.remoteProdToolsDockCtrl.loadChangeStyleWidget()
        self.action = self.qgisCtrl.createAction(
            Config.NAME,
            self.getPluginIconPath(),
            self.startPlugin   
        )
        self.qgisCtrl.addActionToolBar(self.action)
        self.toggle_buffer = self.qgisCtrl.createAction(
            "Desligar Buffer",
            self.getToggleBufferIconPath(),
            self.toggleBuffer
        )
        self.qgisCtrl.addActionToolBar(self.toggle_buffer)
        self.toggle_vertices = self.qgisCtrl.createAction(
            "Desligar Vértices",
            self.getToggleVerticesIconPath(),
            self.toggleVertices
        )
        self.qgisCtrl.addActionToolBar(self.toggle_vertices)
        self.qgisCtrl.loadProcessingProvider(self.getPluginIconPath())
        
        
    def unload(self):
        self.remoteProdToolsDockCtrl.unload()
        self.localProdToolsDockCtrl.unload()
        self.prodToolsSettingsCtrl.unload()
        self.qgisCtrl.removeActionToolBar(self.action)
        self.qgisCtrl.removeActionToolBar(self.toggle_buffer)
        self.qgisCtrl.removeActionToolBar(self.toggle_vertices)
        self.qgisCtrl.removeWidget(self.widget)
        self.qgisCtrl.unload()
        
    def startPlugin(self, b):
        self.loginCtrl.showView()
         
    def toggleBuffer(self):
        toggle("Buffer", self.toggle_buffer_pressed)
        self.toggle_buffer_pressed = not self.toggle_buffer_pressed 

    def toggleVertices(self):
        toggle("Vértices", self.toggle_vertices_pressed)
        self.toggle_vertices_pressed = not self.toggle_vertices_pressed 


    def startPluginExternally(self, activityData):
        if self.remoteProdToolsDockCtrl:
            self.remoteProdToolsDockCtrl.closedDock()
        remoteSapCtrl = RemoteSapCtrl( self.qgisCtrl )
        remoteSapCtrl.setupActivityDataModelExternally( activityData )
        productionTools = self.remoteProdToolsDockCtrl.loadDockWidgetExternally( 
            remoteSapCtrl.getActivityDataModel(),
            remoteSapCtrl
        )
        widget = productionTools.getActivityWidget('Atividade:')
        if not widget:
            return
        widget.hideButtons(True)

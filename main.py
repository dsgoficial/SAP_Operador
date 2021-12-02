import os, sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


from .controllers.loginCtrl import LoginCtrl
from .controllers.remoteProdToolsDockCtrl import RemoteProdToolsDockCtrl
from .controllers.localProdToolsDockCtrl import LocalProdToolsDockCtrl
from .controllers.prodToolsSettingsCtrl import ProdToolsSettingsCtrl

from .modules.sap.controllers.remoteSapCtrl import RemoteSapCtrl
from .modules.sap.controllers.localSapCtrl import LocalSapCtrl
from .modules.pluginUpdater.controllers.updaterCtrl import UpdaterCtrl

from .modules.qgis.qgisCtrl import QgisCtrl
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
        self.qgisCtrl = QgisCtrl()
        self.externalInstance = None
        self.updaterCtrl = UpdaterCtrl( self.qgisCtrl )
        self.prodToolsSettingsCtrl = ProdToolsSettingsCtrl( 
            self.qgisCtrl,
            self.updaterCtrl 
        )
        self.remoteProdToolsDockCtrl = RemoteProdToolsDockCtrl(
            sap=RemoteSapCtrl( self.qgisCtrl ),
            qgis=self.qgisCtrl,
            databaseFactory=DatabaseFactory(),
            processingFactoryDsgTools=ProcessingQgisFactory(),
            fme=FmeApiSingleton.getInstance(),
            pomodoro=None, #Pomodoro( iface ),
            prodToolsSettings=self.prodToolsSettingsCtrl,
            toolFactoryDsgTools=ToolFactory()
        )
        self.localProdToolsDockCtrl = LocalProdToolsDockCtrl(
            sap=LocalSapCtrl( self.qgisCtrl ),
            qgis=self.qgisCtrl,
            databaseFactory=DatabaseFactory(),
            processingFactoryDsgTools=ProcessingQgisFactory(),
            prodToolsSettings=self.prodToolsSettingsCtrl
        )
        self.loginCtrl = LoginCtrl(
            qgis=self.qgisCtrl,
            remoteProdToolsDockCtrl=self.remoteProdToolsDockCtrl,
            localProdToolsDockCtrl=self.localProdToolsDockCtrl
        )
    
    def getPluginIconPath(self):
        return os.path.join(
            os.path.abspath(os.path.join(
                os.path.dirname(__file__)
            )),
            'icons',
            'production.png'
        )

    def initGui(self):
        self.qgisCtrl.load()
        self.action = self.qgisCtrl.createAction(
            Config.NAME,
            self.getPluginIconPath(),
            self.startPlugin   
        )
        self.qgisCtrl.addActionToolBar(self.action)
        self.qgisCtrl.loadProcessingProvider(self.getPluginIconPath())
        self.prodToolsSettingsCtrl.load()
        
    def unload(self):
        self.remoteProdToolsDockCtrl.unload()
        self.localProdToolsDockCtrl.unload()
        self.prodToolsSettingsCtrl.unload()
        self.qgisCtrl.unload()
        
    def startPlugin(self, b):
        self.loginCtrl.showView()

    def startPluginExternally(self, activityData):
        if self.remoteProdToolsDockCtrl:
            self.remoteProdToolsDockCtrl.closedDock()
        remoteSapCtrl = RemoteSapCtrl( self.qgisCtrl )
        remoteSapCtrl.setupActivityDataModel( activityData )
        self.remoteProdToolsDockCtrl.loadDockWidget( 
            remoteSapCtrl.getActivityDataModel()
        )

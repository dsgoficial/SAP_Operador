import os
from Ferramentas_Producao.modules.sap.sapCtrl import SapCtrl
from Ferramentas_Producao.modules.qgis.qgisCtrl import QgisCtrl
from Ferramentas_Producao.productionToolsCtrl import ProductionToolsCtrl
from Ferramentas_Producao.modules.fme.factories.fmeApiSingleton import FmeApiSingleton
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

from Ferramentas_Producao.modules.dsgTools.factories.processingQgisFactory import ProcessingQgisFactory
from Ferramentas_Producao.modules.database.factories.databaseFactory import DatabaseFactory
from Ferramentas_Producao.modules.pomodoro.pomodoro import Pomodoro

from Ferramentas_Producao.config import Config

class Main:

    def __init__(self, iface):    
        super(Main, self).__init__()
        self.plugin_dir = os.path.dirname(__file__)
        self.iface = iface
        self.pomodoro = Pomodoro(self.iface)
        self.qgisCtrl = QgisCtrl()

        self.sapCtrl = SapCtrl(
            qgis=self.qgisCtrl,
            messageFactory=UtilsFactory().createMessageFactory()
        )
        
        self.productionToolsCtrl = ProductionToolsCtrl(
            sap=self.sapCtrl,
            qgis=self.qgisCtrl,
            databaseFactory=DatabaseFactory(),
            processingFactory=ProcessingQgisFactory(),
            fme=FmeApiSingleton.getInstance(),
            messageFactory=UtilsFactory().createMessageFactory(),
            pomodoro=self.pomodoro
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
        self.action = self.qgisCtrl.createAction(
            Config.NAME,
            self.getPluginIconPath(),
            self.startPlugin
            
        )
        self.qgisCtrl.addActionDigitizeToolBar(self.action)
        self.qgisCtrl.loadProcessingProvider(self.getPluginIconPath())
        #self.pomodoro.initGui()
        
    def unload(self):
        self.qgisCtrl.removeActionDigitizeToolBar(self.action)
        self.qgisCtrl.unloadProcessingProvider()
        self.productionToolsCtrl.unload()
        self.pomodoro.unload()

    def startPlugin(self, s):
        if not self.sapCtrl.login():
            return
        self.productionToolsCtrl.loadDockWidget()
from qgis.utils import plugins
import json

class CustomFeatureTool:
    
    def __init__(self, controller):
        self.controller = controller

    def getTool(self):
        try:
            from DsgTools.Modules.acquisitionMenu.controllers.acquisitionMenuCtrl import AcquisitionMenuCtrl
            return AcquisitionMenuCtrl()
        except ImportError:
            raise Exception("O DSGTools não está ativado. Ative o DSGTools e tente novamente.")

    def run(self, menuConfigs):
        acquisitionMenu = self.getTool()
        acquisitionMenu.createMenuDock( menuConfigs )
        return acquisitionMenu

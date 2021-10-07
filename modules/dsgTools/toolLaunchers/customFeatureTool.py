from qgis.utils import plugins
import json

class CustomFeatureTool:
    
    def __init__(self, controller):
        self.controller = controller

    def getTool(self):
        return plugins['DsgTools'].getAcquisitionMenu()

    def run(self, menuConfigs):
        acquisitionMenu = self.getTool()
        acquisitionMenu.createMenuDock( menuConfigs )
        return acquisitionMenu

        

        
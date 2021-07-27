from qgis.utils import plugins

class CustomFeatureTool:
    
    def __init__(self):
        self.checkInstallation()
        self.customFeatureTool = self.getTool()
        
    def checkInstallation(self):
        if 'DsgTools' in plugins:
            raise 'DsgTools não está instalado!'
        try:
            self.getTool()
        except:
            raise 'ferramenta "CustomFeatureTool" não encontrada!'

    def getTool(self):
        return plugins['DsgTools'].guiManager.productionToolsGuiManager.toolBoxesGuiManager.cfToolbox

    def run(self):
        pass
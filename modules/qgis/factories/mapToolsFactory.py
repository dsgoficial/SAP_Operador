from Ferramentas_Producao.modules.qgis.factories.trimLineMapToolSingleton import TrimLineMapToolSingleton
from Ferramentas_Producao.modules.qgis.factories.expandLineMapToolSingleton import ExpandLineMapToolSingleton

class MapToolsFactory:

    def getTool(self, toolName):
        toolNames = {
            'TrimLineMapTool':  TrimLineMapToolSingleton,
            'ExpandLineMapTool':  ExpandLineMapToolSingleton
        }
        return toolNames[toolName].getInstance()
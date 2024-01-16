from Ferramentas_Producao.modules.qgis.factories.trimLineMapToolSingleton import TrimLineMapToolSingleton
from Ferramentas_Producao.modules.qgis.factories.expandLineMapToolSingleton import ExpandLineMapToolSingleton
from Ferramentas_Producao.modules.qgis.factories.convergencePointMapToolSingleton import ConvergencePointMapToolSingleton
from Ferramentas_Producao.modules.qgis.factories.selectErrorSingleton import SelectErrorSingleton

class MapToolsFactory:

    def getTool(self, toolName):
        toolNames = {
            'TrimLineMapTool':  TrimLineMapToolSingleton,
            'ExpandLineMapTool':  ExpandLineMapToolSingleton,
            'ConvergencePoint': ConvergencePointMapToolSingleton,
            'SelectError': SelectErrorSingleton
        }
        return toolNames[toolName].getInstance()
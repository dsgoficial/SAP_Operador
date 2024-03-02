from SAP_Operador.modules.qgis.factories.trimLineMapToolSingleton import TrimLineMapToolSingleton
from SAP_Operador.modules.qgis.factories.expandLineMapToolSingleton import ExpandLineMapToolSingleton
from SAP_Operador.modules.qgis.factories.convergencePointMapToolSingleton import ConvergencePointMapToolSingleton
from SAP_Operador.modules.qgis.factories.selectErrorSingleton import SelectErrorSingleton

class MapToolsFactory:

    def getTool(self, toolName):
        toolNames = {
            'TrimLineMapTool':  TrimLineMapToolSingleton,
            'ExpandLineMapTool':  ExpandLineMapToolSingleton,
            'ConvergencePoint': ConvergencePointMapToolSingleton,
            'SelectError': SelectErrorSingleton
        }
        return toolNames[toolName].getInstance()
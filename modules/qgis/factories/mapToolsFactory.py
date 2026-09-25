from SAP_Operador.modules.qgis.factories.convergencePointMapToolSingleton import ConvergencePointMapToolSingleton
from SAP_Operador.modules.qgis.factories.selectErrorSingleton import SelectErrorSingleton

class MapToolsFactory:

    def getTool(self, toolName):
        toolNames = {
            'ConvergencePoint': ConvergencePointMapToolSingleton,
            'SelectError': SelectErrorSingleton
        }
        return toolNames[toolName].getInstance()
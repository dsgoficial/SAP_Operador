from SAP_Operador.modules.qgis.mapFunctions.smoothLine import SmoothLine
from SAP_Operador.modules.qgis.mapFunctions.closeLine import CloseLine
from SAP_Operador.modules.qgis.mapFunctions.trimLine import TrimLine
from SAP_Operador.modules.qgis.mapFunctions.expandLine import ExpandLine
from SAP_Operador.modules.qgis.mapFunctions.createNewMapView import CreateNewMapView
from SAP_Operador.modules.qgis.mapFunctions.convergencePoint import ConvergencePoint

class MapFunctionsFactory:

    def getFunction(self, functionName):
        functionNames = {
            'SmoothLine':  SmoothLine,
            'CloseLine':  CloseLine,
            'TrimLine':  TrimLine,
            'ExpandLine':  ExpandLine,
            'CreateNewMapView': CreateNewMapView,
            'ConvergencePoint': ConvergencePoint,
        }
        return functionNames[functionName]()
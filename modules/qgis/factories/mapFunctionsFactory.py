from SAP_Operador.modules.qgis.mapFunctions.smoothLine import SmoothLine
from SAP_Operador.modules.qgis.mapFunctions.createNewMapView import CreateNewMapView
from SAP_Operador.modules.qgis.mapFunctions.convergencePoint import ConvergencePoint

class MapFunctionsFactory:

    def getFunction(self, functionName):
        functionNames = {
            'SmoothLine':  SmoothLine,
            'CreateNewMapView': CreateNewMapView,
            'ConvergencePoint': ConvergencePoint,
        }
        return functionNames[functionName]()
from Ferramentas_Producao.modules.qgis.mapFunctions.smoothLine import SmoothLine
from Ferramentas_Producao.modules.qgis.mapFunctions.closeLine import CloseLine
from Ferramentas_Producao.modules.qgis.mapFunctions.trimLine import TrimLine
from Ferramentas_Producao.modules.qgis.mapFunctions.expandLine import ExpandLine
from Ferramentas_Producao.modules.qgis.mapFunctions.createNewMapView import CreateNewMapView
from Ferramentas_Producao.modules.qgis.mapFunctions.convergencePoint import ConvergencePoint
from Ferramentas_Producao.modules.qgis.mapFunctions.selectRaster import SelectRaster

class MapFunctionsFactory:

    def getFunction(self, functionName):
        functionNames = {
            'SmoothLine':  SmoothLine,
            'CloseLine':  CloseLine,
            'TrimLine':  TrimLine,
            'ExpandLine':  ExpandLine,
            'CreateNewMapView': CreateNewMapView,
            'ConvergencePoint': ConvergencePoint,
            'SelectRaster': SelectRaster
        }
        return functionNames[functionName]()
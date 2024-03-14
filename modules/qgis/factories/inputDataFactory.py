from SAP_Operador.modules.qgis.inputs.rasterRemote import RasterRemote
from SAP_Operador.modules.qgis.inputs.rasterLocal import RasterLocal
from SAP_Operador.modules.qgis.inputs.postgis import Postgis
from SAP_Operador.modules.qgis.inputs.message import Message
from SAP_Operador.modules.qgis.inputs.browserUrl import BrowserUrl
from SAP_Operador.modules.qgis.inputs.wms import Wms
from SAP_Operador.modules.qgis.inputs.wfs import Wfs
from SAP_Operador.modules.qgis.inputs.virtualLayer import VirtualLayer
from SAP_Operador.modules.qgis.inputs.arcGisMapServer import ArcGisMapServer

class InputDataFactory:

    def createInputDataType(self, typeNumber):
        types = {
            1: RasterLocal,
            2: RasterRemote,
            3: Postgis,
            4: Message,
            5: BrowserUrl,
            6: Wms,
            7: Wfs,
            8: Wms,
            10: ArcGisMapServer,
            100: VirtualLayer
        }
        if not(typeNumber in types):
            return
        return types[typeNumber]()
from SAP_Operador.modules.qgis.inputs.inputLayer import InputLayer
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets
from qgis.PyQt.QtXml import QDomDocument

class ArcGisMapServer(InputLayer):

    def __init__(self):
        super(ArcGisMapServer, self).__init__()
    
    def load(self, data):
        path = data['caminho']
        layer = core.QgsRasterLayer(f'url={path}', data['nome'], "arcgismapserver")
        layer.setCrs( core.QgsCoordinateReferenceSystem( int(data['epsg']) ) )
        self.addMapLayer( layer, 0 )
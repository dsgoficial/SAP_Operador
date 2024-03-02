from qgis.utils import iface
from qgis import gui, core

from SAP_Operador.modules.qgis.mapFunctions.mapFunction import MapFunction

class SmoothLine(MapFunction):

    def __init__(self):
        super(SmoothLine, self).__init__()
    
    def isValidParameters(self, layer):
        if not layer:
            return (False, 'Selecione uma camada')
        if not(layer.crs().mapUnits() == core.QgsUnitTypes.DistanceMeters):
            return (False, 'A camada ativa deve ter sua unidade de distancia em metros')
        if not(layer.geometryType() == core.QgsWkbTypes.LineGeometry):
            return (False, 'A camada ativa deve ser do tipo "LineGeometry"')
        if not(layer.isEditable()):
            return (False, 'A camada ativa deve está no modo editável')
        if not(len(layer.selectedFeatures()) > 0):
            return (False, 'Selecione no mínimo uma feição')
        return (True, '')

    def run(self, layer):
        result = self.isValidParameters(layer)
        if not result[0]:
            return result
        for feat in layer.selectedFeatures():
            geom = feat.geometry()
            geom_smooth = geom.smooth(2, 0.3)
            feat.setGeometry(geom_smooth)
            layer.updateFeature(feat)
        iface.mapCanvas().refresh()
        return (True, '')

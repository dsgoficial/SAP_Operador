from qgis.utils import iface
from qgis import gui, core
import math

from SAP_Operador.modules.qgis.mapFunctions.mapFunction import MapFunction

class CloseLine(MapFunction):

    def __init__(self):
        super(CloseLine, self).__init__()
    
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
        modifiedFeatures = []
        for feat in layer.selectedFeatures():
            geom = feat.geometry()
            vertexList = geom.asPolyline()
            x1 = vertexList[0][0]
            y1 = vertexList[0][1]
            x2 = vertexList[-1][0]
            y2 = vertexList[-1][1]
            distance = (math.sqrt ((x1 - x2)**2 + (y1 - y2)**2))
            if(not distance <= 50):
                return (False, 'Distância entre vertice final e inicial deve ser menor que a tolerância de 50 metros.') 
            idxLastVertex = len(vertexList)-1
            lastVertex = geom.vertexAt(idxLastVertex)
            geom.moveVertex(x1, y1, idxLastVertex)
            geom.insertVertex(lastVertex.x(), lastVertex.y(), idxLastVertex)
            feat.setGeometry(geom)
            modifiedFeatures.append(feat)
        [ layer.updateFeature(feat) for feat in modifiedFeatures ]
        iface.mapCanvas().refresh()
        return (True, '')

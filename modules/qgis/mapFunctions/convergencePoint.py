from qgis.utils import iface
from qgis import gui, core
import math
from SAP_Operador.modules.qgis.mapFunctions.mapFunction import MapFunction

class ConvergencePoint(MapFunction):

    def __init__(self):
        super(ConvergencePoint, self).__init__()

    def run(self, geometryFilter, parameters):
        validOutputTmp = []
        for data in parameters:
            layer =  data['layer']
            validFeatures = []
            ct = iface.mapCanvas().mapSettings().layerTransform( layer )
            geometryFilter.transform(ct, core.QgsCoordinateTransform.ReverseTransform)
            geometryFilterEngine = core.QgsGeometry.createGeometryEngine( geometryFilter.constGet() )
            geometryFilterEngine.prepareGeometry()
            centroid = geometryFilterEngine.centroid()
            for feature in data['features']:
                geometryFeature = feature.geometry()
                nCoords = geometryFeature.constGet().nCoordinates()
                selectedPoints = []
                indexesToMove = []
                indexesToDelete = []
                for idx in range(nCoords):
                    point = geometryFeature.vertexAt( idx )
                    if not geometryFilterEngine.contains( point ):
                        continue
                    if point in selectedPoints:
                        indexesToDelete.append(idx)
                        continue
                    selectedPoints.append(point)
                    indexesToMove.append(idx)
                for index in indexesToMove:
                    geometryFeature.moveVertex( centroid, index)
                for index in sorted(indexesToDelete, reverse=True):
                    geometryFeature.deleteVertex(index)
                if not geometryFeature.isGeosValid():
                    return (False, 'A operação gerou geometrias inválidas. Revise sua seleção e tente novamente.')
                feature.setGeometry(geometryFeature)
                validFeatures.append(feature)
            validOutputTmp.append({'layer': layer, 'features': validFeatures})
        [ 
            [ data['layer'].updateFeature(feature) for feature in data['features']]
            for data in validOutputTmp
        ]
        iface.mapCanvas().refresh()
        return (True, '')

from qgis.utils import iface
from qgis import gui, core
import math
from SAP_Operador.modules.qgis.mapFunctions.mapFunction import MapFunction

class ExpandLine(MapFunction):

    def __init__(self):
        super(ExpandLine, self).__init__()

    def run(self, featureToExpandId, featureTargetId, distance):
        layer = iface.activeLayer()
        featureToExpand = self.getFeatureById(layer, featureToExpandId)
        featureTarget = self.getFeatureById(layer, featureTargetId)
        if self.intersectingGeometries(featureToExpand.geometry(), featureTarget.geometry()):
            return (True, '')           
        penultimatePointIdx, lastPointIdx = self.getPointsIndexOfTheNearestSegment(
            featureToExpand, 
            featureTarget
        )
        penultimatePoint = featureToExpand.geometry().vertexAt(penultimatePointIdx)
        lastPoint = featureToExpand.geometry().vertexAt(lastPointIdx)
        angle = math.atan((lastPoint.y() - penultimatePoint.y())/(lastPoint.x() - penultimatePoint.x()))
        coordX = lastPoint.x() + distance * math.cos(angle) 
        coordY = lastPoint.y() + distance * math.sin(angle)
        layer.moveVertex(coordX, coordY, featureToExpandId, lastPointIdx)
        layer.commitChanges()
        layer.startEditing()
        return (True, '')

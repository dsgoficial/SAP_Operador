from qgis.utils import iface
from qgis import gui, core
import processing
from Ferramentas_Producao.modules.qgis.mapFunctions.mapFunction import MapFunction

class TrimLine(MapFunction):

    def __init__(self):
        super(TrimLine, self).__init__()

    def run(self, featureToTrimId, featureTargetId, distance):
        layer = iface.activeLayer()
        featureToTrim = self.getFeatureById(layer, featureToTrimId)
        featureTarget = self.getFeatureById(layer, featureTargetId)
        pointIntersection = featureToTrim.geometry().intersection(featureTarget.geometry()).asPoint()
        pointIntersection = core.QgsPoint(round(pointIntersection.x(), 5), round(pointIntersection.y(), 5))
        attributes = featureToTrim.attributes()
        attributes[0] = None
        layer.startEditing()
        if not self.intersectingGeometries(featureToTrim.geometry(), featureTarget.geometry()):
            return (False, 'Não há interseção entre as feições selecionadas! Escolha outra feição')     
        success, splits, topo = featureToTrim.geometry().splitGeometry(
            featureTarget.geometry().asPolyline(), 
            True
        )
        splitFeatureId = None
        splitGeometry = splits[0]
        differenceGeometry = featureToTrim.geometry().difference(splitGeometry)
        if differenceGeometry.equals(featureToTrim.geometry()):
            beforeFeatureIds = layer.allFeatureIds()
            self.addFeature(attributes, splitGeometry, layer)
            self.saveChanges(layer)
            splitFeatureId = list(set(layer.allFeatureIds()) - set(beforeFeatureIds))[0]
            differenceGeometry = self.customDifference(attributes, featureToTrimId, splitFeatureId, layer)
        if splitGeometry.length() > distance and differenceGeometry.length() > distance:
            self.removeFeature(splitFeatureId, layer)
            self.saveChanges(layer)
            return (False, 'As linhas selecionadas excedem a tolerância definida ou não respeitam as condições necessárias para a execução')
        layer.deleteFeature(featureToTrim.id())
        if differenceGeometry.length() <= distance:
            self.saveChanges(layer)
            return (True, '')
        self.removeFeature(splitFeatureId, layer) if splitFeatureId else ''
        penultimatePointIdx, lastPointIdx = self.getPointsIndexOfTheNearestSegment(
            featureToTrim, 
            featureTarget
        )
        differenceGeometry.moveVertex(pointIntersection, lastPointIdx)
        self.addFeature(attributes, differenceGeometry, layer)
        self.saveChanges(layer)
        return (True, '')

    def customDifference(self, attributes, featureToTrimId, splitFeatureId, layer):
        self.selectFeaturesByIds(layer, [splitFeatureId, featureToTrimId])
        result = processing.run(
            'native:dissolve', 
            { 
                'FIELD' : [], 
                'INPUT' : core.QgsProcessingFeatureSourceDefinition(layer.id(), True), 
                'OUTPUT' : 'TEMPORARY_OUTPUT' 
            }
        )
        self.deselectFeaturesByIds(layer, [splitFeatureId, featureToTrimId])
        dissolveFeature = result['OUTPUT'].getFeature(result['OUTPUT'].allFeatureIds()[0])
        polylineGeometries = [
            core.QgsGeometry.fromPolyline([core.QgsPoint(point.x(), point.y()) for point in polyline])
            for polyline in dissolveFeature.geometry().asMultiPolyline()
        ]
        featureToTrim = self.getFeatureById(layer, featureToTrimId)
        splitFeature = self.getFeatureById(layer, splitFeatureId)
        for polylineGeom in polylineGeometries:
            if not polylineGeom.overlaps(featureToTrim.geometry()):
                continue
            return polylineGeom.difference(splitFeature.geometry())

    def selectFeaturesByIds(self, layer, featureIds):
        [ layer.select(featureId) for featureId in featureIds ]

    def deselectFeaturesByIds(self, layer, featureIds):
        [ layer.select(featureId) for featureId in featureIds ]

    def saveChanges(self, layer):
        layer.commitChanges()
        layer.startEditing()

    def addFeature(self, attributes, geometry, layer):
        feat = core.QgsFeature()
        feat.setAttributes(attributes)
        feat.setGeometry(geometry)
        layer.addFeature(feat)

    def removeFeature(self, featureId, layer):
        layer.deleteFeature(featureId) if featureId and featureId in layer.allFeatureIds() else ''
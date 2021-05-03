from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QColor
from qgis.PyQt.Qt import QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsFeature,
                       QgsDataSourceUri,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsWkbTypes,
                       QgsAction,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingUtils,
                       QgsSpatialIndex,
                       QgsGeometry,
                       QgsProcessingParameterField,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterExpression,
                       QgsProcessingException,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterType,
                       QgsProcessingParameterCrs,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsField,
                       QgsFields,
                       QgsProcessingOutputMultipleLayers,
                       QgsProcessingParameterString,
                       QgsConditionalStyle,
                       QgsVectorLayer)
import os
from qgis.utils import iface
import re

class ProcessingAlg(QgsProcessingAlgorithm):

    def initAlgorithm(self, config):
        raise NotImplementedError('Abstract Method')

    def processAlgorithm(self, parameters, context, feedback):
        raise NotImplementedError('Abstract Method')

    def getFlagGeometry(self, feature):
        if QgsWkbTypes.geometryType(feature.geometry().wkbType()) == QgsWkbTypes.LineGeometry:
            multiPoints = feature.geometry().convertToType(0, True)
            pointList = multiPoints.asMultiPoint()
            return QgsGeometry.fromPointXY(pointList[int(len(pointList)/2)])
        else:
            return feature.geometry().centroid()

    def createFlagLayer(self, parameters, context):
        return self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            self.getFlagFields(),
            self.getFlagWkbType(),
            iface.mapCanvas().mapSettings().destinationCrs()
        )

    def getFlagWkbType(self):
        raise NotImplementedError('Abstract Method')

    def createFlagFeature(self, attributes, geometry):
        feat = QgsFeature(self.getFlagFields())
        for attrName in attributes:
            feat.setAttribute(attrName, attributes[attrName])
        feat.setGeometry(geometry)
        return feat

    def getFlagFields(self):
        raise NotImplementedError('Abstract Method')

    def getAttributeIndex(self, attributeName, layer):
        for attrName, attrAlias  in list(layer.attributeAliases().items()):
            if not(attributeName in [attrName, attrAlias]):
                continue
            if layer.fields().indexOf(attrName) < 0:
                return layer.fields().indexOf(attrAlias)
            return layer.fields().indexOf(attrName) 
        return -1

    def name(self):
        raise NotImplementedError('Abstract Method')

    def displayName(self):
        raise NotImplementedError('Abstract Method')

    def group(self):
        raise NotImplementedError('Abstract Method')

    def groupId(self):
        raise NotImplementedError('Abstract Method')

    def tr(self, string):
        raise NotImplementedError('Abstract Method')

    def createInstance(self):
        raise NotImplementedError('Abstract Method')
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
                       QgsProcessingParameterFolderDestination,
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
from SAP_Operador.modules.qgis.processingAlgs.processingAlg import ProcessingAlg

class LoadShapefilesAlg(ProcessingAlg):

    FOLDER_SHAPEFILES = 'FOLDER_SHAPEFILES'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super(LoadShapefilesAlg, self).__init__()

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFile(
                self.FOLDER_SHAPEFILES,
                self.tr('Pasta com Shapefiles'),
                behavior = QgsProcessingParameterFile.Folder,
            )
        )

        self.addOutput(
            QgsProcessingOutputMultipleLayers(
                self.OUTPUT,
                self.tr('Loaded layers')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        folderPath = self.parameterAsString(
            parameters,
            self.FOLDER_SHAPEFILES,
            context
        )
        output = []
        shapefileData = [ 
            {
                'name': fileName.split('.')[0],
                'path': os.path.join(folderPath, fileName)
            }
            for fileName in os.listdir(folderPath)
            if fileName.split('.')[1] == 'shp'
        ]
        shapefileData = sorted(shapefileData, key=lambda k: k['name']) 
        listSize = len(shapefileData)
        progressStep = 100/listSize if listSize else 0
        rootNode = QgsProject.instance().layerTreeRoot().addGroup('shapefiles')
        groups = {
            QgsWkbTypes.PointGeometry: self.createGroup('Ponto', rootNode),
            QgsWkbTypes.LineGeometry: self.createGroup('Linha', rootNode),
            QgsWkbTypes.PolygonGeometry: self.createGroup('Area', rootNode),
            
        }
        for step, data in enumerate(shapefileData):
            if feedback.isCanceled():
                break
            iface.mapCanvas().freeze(True)
            ml = QgsProject.instance().addMapLayer(
                QgsVectorLayer(data['path'], data['name'], 'ogr'), 
                addToLegend = False
            )
            groups[QgsWkbTypes.geometryType(ml.wkbType())].addLayer(ml)
            output.append(ml.id())
            iface.mapCanvas().freeze(False)
            feedback.setProgress(step*progressStep)
        self.removeEmptyGroups(list(groups.values()), rootNode)
        return {self.OUTPUT: output}

    def createGroup(self, groupName, rootNode):
        return rootNode.addGroup(groupName)
       
    def removeEmptyGroups(self, groups, rootNode):
        for group in groups:
            if group.findLayers():
                continue
            rootNode.removeChildNode(group)

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def name(self):
        return 'loadshapefiles'

    def displayName(self):
        return self.tr('Carregar shapefiles')

    def group(self):
        return self.tr('Outros')

    def groupId(self):
        return 'SAP Operador: Outros'

    def tr(self, string):
        return QCoreApplication.translate('LoadShapefilesAlg', string)

    def createInstance(self):
        return LoadShapefilesAlg()
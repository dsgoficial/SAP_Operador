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
import uuid
from qgis.utils import iface
from Ferramentas_Producao.modules.qgis.processingAlgs.processingAlg import ProcessingAlg

class UuidCheckerAlg(ProcessingAlg):

    INPUT_LAYERS = 'INPUT_LAYERS'
    ATTRIBUTE_NAME = 'ATTRIBUTE_NAME'
    CORRECT = 'CORRECT'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super(UuidCheckerAlg, self).__init__()

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Camadas'),
                QgsProcessing.TypeVectorAnyGeometry
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.ATTRIBUTE_NAME,
                description =  self.tr('Nome do Atributo'),
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CORRECT,
                self.tr('Corrigir')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('uuid_flags')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        inputLyrList = self.parameterAsLayerList(
            parameters,
            self.INPUT_LAYERS,
            context
        )
        attributeName = self.parameterAsFile(
            parameters,
            self.ATTRIBUTE_NAME,
            context
        )
        correct = self.parameterAsBool(
            parameters,
            self.CORRECT,
            context
        )
        output_dest_id = ''
        uuids = []
        errors = []
        listSize = len(inputLyrList)
        progressStep = 100/listSize if listSize else 0
        for step, layer in enumerate(inputLyrList):
            attributeIndex = self.getAttributeIndex(attributeName, layer)
            if attributeIndex < 0:
                continue
            if correct:
                layer.startEditing()
            for feature in layer.getFeatures():
                if feedback.isCanceled():
                    return {self.OUTPUT: output_dest_id}
                attributeValue = feature[attributeIndex]
                isValidUuid = self.isValidUuid(attributeValue)
                hasDuplicateValues = self.hasDuplicateValues(attributeValue, uuids)
                if isValidUuid and not hasDuplicateValues:
                    uuids.append(attributeValue)
                    continue
                if correct:
                    feature[attributeIndex] = str(uuid.uuid4())
                    layer.updateFeature(feature)
                    continue
                [
                    errors.append({
                        'geometry': self.getFlagGeometry(feature),
                        'fields' : {'erro': descr}
                    })
                    for descr, hasError in [
                        ('uuid inválido', not isValidUuid),
                        ('uuid duplicado', hasDuplicateValues)
                    ]
                    if hasError
                ]
            feedback.setProgress(step*progressStep)
        if not correct and len(errors) > 0:
            (output_sink, output_dest_id) = self.createFlagLayer(parameters, context)
            for error in errors:
                output_sink.addFeature(
                    self.createFlagFeature(error['fields'], error['geometry'])
                )
        return {self.OUTPUT: output_dest_id}

    def getFlagWkbType(self):
        return QgsWkbTypes.Point

    def getFlagFields(self):
        sinkFields = QgsFields()
        sinkFields.append(QgsField('erro', QVariant.String))
        return sinkFields

    def hasDuplicateValues(self, value, valueList):
        return value in valueList

    def isValidUuid(self, uuidToTest, version=4):
        try:
            uuidObj = uuid.UUID(uuidToTest, version=version)
        except:
            return False
        return str(uuidObj) == uuidToTest

    def name(self):
        return 'uuidchecker'

    def displayName(self):
        return self.tr('Verificador de UUID')

    def group(self):
        return self.tr('Outros')

    def groupId(self):
        return 'FP: Outros'

    def tr(self, string):
        return QCoreApplication.translate('UuidCheckerAlg', string)

    def createInstance(self):
        return UuidCheckerAlg()
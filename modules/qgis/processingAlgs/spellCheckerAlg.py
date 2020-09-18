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
from Ferramentas_Producao.modules.qgis.processingAlgs.processingAlg import ProcessingAlg
from Ferramentas_Producao.modules.spellchecker.spellchecker import SpellChecker
import re

class SpellCheckerAlg(ProcessingAlg):

    INPUT_LAYERS = 'INPUT_LAYERS'
    ATTRIBUTE_NAME = 'ATTRIBUTE_NAME'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super(SpellCheckerAlg, self).__init__()

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
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('digitacao_flags')
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
        spell = SpellChecker()
        errors = []
        regex = re.compile(r"\s*[^A-Za-z]+\s*")
        output_dest_id = ''
        listSize = len(inputLyrList)
        progressStep = 100/listSize if listSize else 0
        for step, layer in enumerate(inputLyrList):
            attributeIndex = self.getAttributeIndex(attributeName, layer)
            if attributeIndex < 0:
                continue
            for feature in layer.getFeatures():
                if feedback.isCanceled():
                    return {self.OUTPUT: output_dest_id}
                attributeValue = feature[attributeIndex]
                if not attributeValue:
                    continue
                attributeValue = regex.sub(' ', attributeValue)
                wordlist = attributeValue.split()
                misspelled = spell.unknown(wordlist)
                if not(len(misspelled) > 0):
                    continue
                [
                    errors.append({
                        'geometry': self.getFlagGeometry(feature),
                        'fields': {
                            'erro': word,
                            'correcao': spell.correction(word),
                            'outras_opcoes': ','.join(list(spell.candidates(word)))
                        }
                    })
                    for word in misspelled
                ]
            feedback.setProgress(step*progressStep)
        if len(errors) > 0:
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
        sinkFields.append(QgsField('correcao', QVariant.String))
        sinkFields.append(QgsField('outras_opcoes', QVariant.String))
        return sinkFields

    def name(self):
        return 'spellchecker'

    def displayName(self):
        return self.tr('Verificador de Palavras')

    def group(self):
        return self.tr('Outros')

    def groupId(self):
        return 'FP: Outros'

    def tr(self, string):
        return QCoreApplication.translate('SpellCheckerAlg', string)

    def createInstance(self):
        return SpellCheckerAlg()
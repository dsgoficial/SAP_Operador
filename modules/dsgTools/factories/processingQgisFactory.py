from Ferramentas_Producao.modules.dsgTools.interfaces.IProcessingFactory import IProcessingFactory
from Ferramentas_Producao.modules.dsgTools.processing.loadLayersFromPostgis import LoadLayersFromPostgis
from Ferramentas_Producao.modules.dsgTools.processing.groupLayers import GroupLayers
from Ferramentas_Producao.modules.dsgTools.processing.assingFilterToLayers import AssingFilterToLayers
from Ferramentas_Producao.modules.dsgTools.processing.matchAndApplyQmlStylesToLayers import MatchAndApplyQmlStylesToLayers
from Ferramentas_Producao.modules.dsgTools.processing.assignValueMapToLayers import AssignValueMapToLayers
from Ferramentas_Producao.modules.dsgTools.processing.assignMeasureColumnToLayers import AssignMeasureColumnToLayers
from Ferramentas_Producao.modules.dsgTools.processing.assignAliasesToLayers import AssignAliasesToLayers
from Ferramentas_Producao.modules.dsgTools.processing.assignActionsToLayers import AssignActionsToLayers
from Ferramentas_Producao.modules.dsgTools.processing.assignDefaultFieldValueToLayers import AssignDefaultFieldValueToLayers
from Ferramentas_Producao.modules.dsgTools.processing.assignExpressionFieldToLayers import AssignExpressionFieldToLayers
from Ferramentas_Producao.modules.dsgTools.processing.assignConditionalStyleToLayers import AssignConditionalStyleToLayers
from Ferramentas_Producao.modules.dsgTools.processing.runFMESAP import RunFMESAP
from Ferramentas_Producao.modules.dsgTools.processing.ruleStatistics import RuleStatistics


class ProcessingQgisFactory(IProcessingFactory):

    def __init__(self):
        super(ProcessingQgisFactory, self).__init__()

    def createProcessing(self, processingName, mediator):
        processingNames = {
            'LoadLayersFromPostgis': LoadLayersFromPostgis,
            'GroupLayers': GroupLayers,
            'AssingFilterToLayers': AssingFilterToLayers,
            'MatchAndApplyQmlStylesToLayers': MatchAndApplyQmlStylesToLayers,
            'AssignValueMapToLayers': AssignValueMapToLayers,
            'AssignMeasureColumnToLayers': AssignMeasureColumnToLayers,
            'AssignAliasesToLayers': AssignAliasesToLayers,
            'AssignActionsToLayers': AssignActionsToLayers,
            'AssignDefaultFieldValueToLayers': AssignDefaultFieldValueToLayers,
            'AssignExpressionFieldToLayers': AssignExpressionFieldToLayers,
            'AssignConditionalStyleToLayers': AssignConditionalStyleToLayers,
            'RuleStatistics': RuleStatistics,
            'RunFMESAP': RunFMESAP
        }
        return processingNames[processingName](mediator)
            
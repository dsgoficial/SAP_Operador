from Ferramentas_Producao.modules.dsgTools.interfaces.IProcessingFactory import IProcessingFactory
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.loadLayersFromPostgis import LoadLayersFromPostgis
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.groupLayers import GroupLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.assingFilterToLayers import AssingFilterToLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.matchAndApplyQmlStylesToLayers import MatchAndApplyQmlStylesToLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.assignValueMapToLayers import AssignValueMapToLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.assignMeasureColumnToLayers import AssignMeasureColumnToLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.assignAliasesToLayers import AssignAliasesToLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.assignActionsToLayers import AssignActionsToLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.assignDefaultFieldValueToLayers import AssignDefaultFieldValueToLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.assignExpressionFieldToLayers import AssignExpressionFieldToLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.assignConditionalStyleToLayers import AssignConditionalStyleToLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.runFMESAP import RunFMESAP
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.ruleStatistics import RuleStatistics
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.setRemoveDuplicateNodePropertyOnLayers import SetRemoveDuplicateNodePropertyOnLayers
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.assignFormatRulesToLayers import AssignFormatRulesToLayers


class ProcessingQgisFactory(IProcessingFactory):

    def __init__(self):
        super(ProcessingQgisFactory, self).__init__()

    def createProcessing(self, processingName, controller):
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
            'RunFMESAP': RunFMESAP,
            'SetRemoveDuplicateNodePropertyOnLayers': SetRemoveDuplicateNodePropertyOnLayers,
            'AssignFormatRulesToLayers': AssignFormatRulesToLayers,
        }
        return processingNames[processingName](controller)
            
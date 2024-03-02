from SAP_Operador.modules.dsgTools.interfaces.IProcessingFactory import IProcessingFactory
from SAP_Operador.modules.dsgTools.processingLaunchers.loadLayersFromPostgis import LoadLayersFromPostgis
from SAP_Operador.modules.dsgTools.processingLaunchers.groupLayers import GroupLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.assingFilterToLayers import AssingFilterToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.matchAndApplyQmlStylesToLayers import MatchAndApplyQmlStylesToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.assignValueMapToLayers import AssignValueMapToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.assignMeasureColumnToLayers import AssignMeasureColumnToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.assignAliasesToLayers import AssignAliasesToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.assignActionsToLayers import AssignActionsToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.assignDefaultFieldValueToLayers import AssignDefaultFieldValueToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.assignExpressionFieldToLayers import AssignExpressionFieldToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.assignConditionalStyleToLayers import AssignConditionalStyleToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.runFMESAP import RunFMESAP
from SAP_Operador.modules.dsgTools.processingLaunchers.ruleStatistics import RuleStatistics
from SAP_Operador.modules.dsgTools.processingLaunchers.setRemoveDuplicateNodePropertyOnLayers import SetRemoveDuplicateNodePropertyOnLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.assignFormatRulesToLayers import AssignFormatRulesToLayers
from SAP_Operador.modules.dsgTools.processingLaunchers.createReviewGrid import CreateReviewGrid
from SAP_Operador.modules.dsgTools.processingLaunchers.loadThemes import LoadThemes
from SAP_Operador.modules.dsgTools.processingLaunchers.genericSelectionToolParameters import GenericSelectionToolParameters

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
            'CreateReviewGrid': CreateReviewGrid,
            'LoadThemes': LoadThemes,
            'GenericSelectionToolParameters': GenericSelectionToolParameters
        }
        return processingNames[processingName](controller)
            
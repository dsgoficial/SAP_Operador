from SAP_Operador.modules.dsgTools.toolLaunchers.customFeatureTool import CustomFeatureTool
from SAP_Operador.modules.dsgTools.toolbarLaunchers.reviewToolbar import ReviewToolBar
from SAP_Operador.modules.dsgTools.toolLaunchers.workflowToolbox import WorkflowToolBox

class ToolFactory:

    def __init__(self):
        super(ToolFactory, self).__init__()

    def getTool(self, toolName, controller):
        toolNames = {
            'CustomFeatureTool': CustomFeatureTool,
            'ReviewToolBar': ReviewToolBar,
            'WorkflowToolBox': WorkflowToolBox
        }
        return toolNames[toolName](controller)
            
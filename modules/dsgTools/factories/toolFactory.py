from Ferramentas_Producao.modules.dsgTools.toolLaunchers.customFeatureTool import CustomFeatureTool
from Ferramentas_Producao.modules.dsgTools.toolbarLaunchers.reviewToolbar import ReviewToolBar
from Ferramentas_Producao.modules.dsgTools.toolLaunchers.qaToolbox import QAToolBox

class ToolFactory:

    def __init__(self):
        super(ToolFactory, self).__init__()

    def getTool(self, toolName, controller):
        toolNames = {
            'CustomFeatureTool': CustomFeatureTool,
            'ReviewToolBar': ReviewToolBar,
            'QAToolBox': QAToolBox
        }
        return toolNames[toolName](controller)
            
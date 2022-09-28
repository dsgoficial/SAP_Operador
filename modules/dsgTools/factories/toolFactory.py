from Ferramentas_Producao.modules.dsgTools.toolLaunchers.customFeatureTool import CustomFeatureTool
from Ferramentas_Producao.modules.dsgTools.toolbarLaunchers.reviewToolbar import ReviewToolBar

class ToolFactory:

    def __init__(self):
        super(ToolFactory, self).__init__()

    def getTool(self, toolName, controller):
        toolNames = {
            'CustomFeatureTool': CustomFeatureTool,
            'ReviewToolBar': ReviewToolBar,
        }
        return toolNames[toolName](controller)
            
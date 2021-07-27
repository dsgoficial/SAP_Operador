from Ferramentas_Producao.modules.dsgTools.toolLaunchers.customFeatureTool import CustomFeatureTool

class ToolFactory:

    def __init__(self):
        super(ToolFactory, self).__init__()

    def getTool(self, toolName, controller):
        toolNames = {
            'CustomFeatureTool': CustomFeatureTool
        }
        return toolNames[toolName](controller)
            
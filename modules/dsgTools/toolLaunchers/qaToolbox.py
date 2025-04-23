from qgis.utils import plugins
import json

class workflowToolBox:
    
    def __init__(self, controller):
        self.controller = controller

    def getTool(self):
        toolboxManager = self.getManager()
        workflowToolBox = toolboxManager.workflowToolBox
        if workflowToolBox is not None:
            return workflowToolBox
        return self.refreshToolboxObject()

    def getManager(self):
        return plugins['DsgTools'].guiManager.productionToolsGuiManager.toolBoxesGuiManager

    def run(self, workflowDictList):
        workflowToolBox = self.getTool()
        # hide import button
        workflowToolBox.showEditionButton(False)
        # import payload
        workflowToolBox.importWorkflowFromJsonPayload(workflowDictList)
        # show interface
        toolboxManager = self.getManager()
        toolboxManager.showWorkflowToolBox()
        return workflowToolBox

    def refreshToolboxObject(self):
        toolboxManager = self.getManager()
        return toolboxManager.refreshWorkflowToolBoxObject()
    
    def allWorkflowsAreFinishedWithoutFlags(self):
        workflowToolBox = self.getTool()
        return workflowToolBox.allWorkflowsAreFinishedWithoutFlags()
        
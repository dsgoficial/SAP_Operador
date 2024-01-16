from qgis.utils import plugins
import json

class QAToolBox:
    
    def __init__(self, controller):
        self.controller = controller

    def getTool(self):
        toolboxManager = self.getManager()
        qaToolBox = toolboxManager.qaToolBox
        if qaToolBox is not None:
            return qaToolBox
        return self.refreshToolboxObject()

    def getManager(self):
        return plugins['DsgTools'].guiManager.productionToolsGuiManager.toolBoxesGuiManager

    def run(self, workflowDictList):
        qaToolBox = self.getTool()
        # hide import button
        qaToolBox.showEditionButton(False)
        # import payload
        qaToolBox.importWorkflowFromJsonPayload(workflowDictList)
        # show interface
        toolboxManager = self.getManager()
        toolboxManager.showQaToolBox()
        return qaToolBox

    def refreshToolboxObject(self):
        toolboxManager = self.getManager()
        return toolboxManager.refreshQaToolBoxObject()
    
    def allWorkflowsAreFinishedWithoutFlags(self):
        qaToolBox = self.getTool()
        return qaToolBox.allWorkflowsAreFinishedWithoutFlags()
        
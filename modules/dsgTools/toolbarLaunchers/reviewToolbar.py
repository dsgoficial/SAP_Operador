from qgis.utils import plugins
import json

class ReviewToolBar:
    
    def __init__(self, controller):
        self.controller = controller

    def getTool(self):
        return plugins['DsgTools'].guiManager.productionToolsGuiManager.toolbarsGuiManager.reviewTool

    def run(self, reviewLayer):
        reviewToolBar = self.getTool()
        reviewToolBar.setState(
            layer=reviewLayer,
            rankFieldName='rank',
            visitedFieldName='visited'
        )
        return reviewToolBar

        

        
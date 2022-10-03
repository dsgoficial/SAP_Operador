from qgis import core
from qgis.utils import plugins
import json

class ReviewToolBar:
    
    def __init__(self, controller):
        self.controller = controller

    def getTool(self):
        return plugins['DsgTools'].guiManager.productionToolsGuiManager.toolbarsGuiManager.reviewTool

    def run(self, gridLayer, outputLayer=None):
        if outputLayer is not None and outputLayer.featureCount() > 0:
            self.populateGridLayerWithOutputLayerFeatures(gridLayer, outputLayer)
        reviewToolBar = self.getTool()
        reviewToolBar.setState(
            layer=gridLayer,
            rankFieldName='rank',
            visitedFieldName='visited'
        )
        return reviewToolBar

    def populateGridLayerWithOutputLayerFeatures(self, gridLayer, outputLayer):
        gridLayer.startEditing()
        gridLayer.beginEditCommand('FP: populando grid')
        gridLayer.addFeatures(
            core.QgsVectorLayerUtils.makeFeaturesCompatible(
                outputLayer.getFeatures(),
                gridLayer
            )
        )
        gridLayer.endEditCommand()
        gridLayer.commitChanges()

        

        
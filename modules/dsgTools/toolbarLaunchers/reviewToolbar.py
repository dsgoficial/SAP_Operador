from qgis import core
from qgis.utils import plugins
import json

class ReviewToolBar:

    RANK_FIELD = 'rank'
    VISITED_FIELD = 'visited'

    def __init__(self, controller):
        self.controller = controller

    def getTool(self):
        return plugins['DsgTools'].guiManager.productionToolsGuiManager.toolbarsGuiManager.reviewTool

    def run(self, gridLayer, outputLayer=None):
        if not self.validateGridLayer(gridLayer):
            return None
        if outputLayer is not None and outputLayer.featureCount() > 0:
            self.populateGridLayerWithOutputLayerFeatures(gridLayer, outputLayer)
        reviewToolBar = self.getTool()
        reviewToolBar.setState(
            layer=gridLayer,
            rankFieldName=self.RANK_FIELD,
            visitedFieldName=self.VISITED_FIELD,
            zoomType=1,
        )
        return reviewToolBar

    def validateGridLayer(self, gridLayer):
        if gridLayer is None:
            return False
        fieldNames = [field.name() for field in gridLayer.fields()]
        missingFields = [
            field
            for field in (self.RANK_FIELD, self.VISITED_FIELD)
            if field not in fieldNames
        ]
        if missingFields:
            self.controller.showErrorMessageBox(
                None,
                'Erro',
                'A camada de grid de revisão "{0}" não possui o(s) campo(s) obrigatório(s): {1}. '
                'Verifique a estrutura da camada antes de iniciar a revisão.'.format(
                    gridLayer.name(), ', '.join(missingFields)
                )
            )
            return False
        return True

    def populateGridLayerWithOutputLayerFeatures(self, gridLayer, outputLayer):
        gridLayer.startEditing()
        gridLayer.beginEditCommand('SAP Operador: populando grid')
        gridLayer.addFeatures(
            core.QgsVectorLayerUtils.makeFeaturesCompatible(
                outputLayer.getFeatures(),
                gridLayer
            )
        )
        gridLayer.endEditCommand()
        gridLayer.commitChanges()

        

        
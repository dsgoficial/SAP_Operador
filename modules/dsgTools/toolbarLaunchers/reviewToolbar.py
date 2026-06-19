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
        self.prepareFieldCombos(reviewToolBar, gridLayer)
        reviewToolBar.setState(
            layer=gridLayer,
            rankFieldName=self.RANK_FIELD,
            visitedFieldName=self.VISITED_FIELD,
            zoomType=1,
        )
        self.ensureFieldSelection(reviewToolBar)
        return reviewToolBar

    def prepareFieldCombos(self, reviewToolBar, gridLayer):
        # Na primeira carga, o setState do DSGTools chama setField() antes de os
        # combos de campo terem recebido a camada (a propagacao do layerChanged
        # do combo de camada nao e sincrona nessa primeira vez), entao a selecao
        # de 'rank'/'visited' nao "pega" e os combos ficam vazios. Fixar a camada
        # diretamente nos combos de campo aqui garante que os campos ja estejam
        # disponiveis quando o setField for chamado.
        for comboName in ('mMapLayerComboBox', 'rankFieldComboBox', 'visitedFieldComboBox'):
            combo = getattr(reviewToolBar, comboName, None)
            if combo is not None:
                combo.setLayer(gridLayer)

    def ensureFieldSelection(self, reviewToolBar):
        # Defensivo: se por timing a selecao do setState nao pegou, reaplica os
        # campos (a camada ja esta definida nos combos neste ponto).
        rankCombo = getattr(reviewToolBar, 'rankFieldComboBox', None)
        if rankCombo is not None and not rankCombo.currentField():
            rankCombo.setField(self.RANK_FIELD)
        visitedCombo = getattr(reviewToolBar, 'visitedFieldComboBox', None)
        if visitedCombo is not None and not visitedCombo.currentField():
            visitedCombo.setField(self.VISITED_FIELD)

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

        

        
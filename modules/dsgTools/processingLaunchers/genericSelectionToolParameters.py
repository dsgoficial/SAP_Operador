from Ferramentas_Producao.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class GenericSelectionToolParameters(Processing):
    
    def __init__(self, controller):
        super(GenericSelectionToolParameters, self).__init__()
        self.processingId = 'dsgtools:genericselectiontoolparametersalgorithm'
        
    def getParameters(self, parameters):
        return { 'VALUE_LIST' : 'aux_grid_revisao_a;Created Review Grid;grid;moldura' }

from SAP_Operador.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class CreateReviewGrid(Processing):
    
    def __init__(self, controller):
        super(CreateReviewGrid, self).__init__()
        self.processingId = 'dsgtools:createreviewgridalgorithm'

    def getParameters(self, parameters):
        return { 
            'INPUT' : parameters['input'],
            'X_GRID_SIZE': parameters['x_grid_size'],
            'Y_GRID_SIZE': parameters['y_grid_size'],
            'RELATED_TASK_ID': parameters['related_task_id'],
            'OUTPUT': 'memory:'
        }
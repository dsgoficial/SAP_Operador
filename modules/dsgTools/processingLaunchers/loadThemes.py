from SAP_Operador.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class LoadThemes(Processing):
    
    def __init__(self, controller):
        super(LoadThemes, self).__init__()
        self.processingId = 'dsgtools:loadthemes'
        
    def getParameters(self, parameters):
        return {
            'FILE': '.json',
            'TEXT': json.dumps(parameters['themes'])
        }
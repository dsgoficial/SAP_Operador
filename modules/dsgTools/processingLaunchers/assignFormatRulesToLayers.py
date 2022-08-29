from Ferramentas_Producao.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class AssignFormatRulesToLayers(Processing):
    
    def __init__(self, controller):
        super(AssignFormatRulesToLayers, self).__init__()
        self.processingId = 'dsgtools:assignformatrulestolayersalgorithm'

    def getParameters(self, parameters):
        uris = []
        for layerId in parameters['layerIds']:
            uri = self.getLayerUriFromId(layerId)
            if not uri:
                continue
            uris.append(uri)
        return {
                'FILE': '.json',
                'TEXT': json.dumps(parameters['rules']),
                'CLEAN_BEFORE_ASSIGN': True,
                'INPUT_LAYERS' : uris
            }

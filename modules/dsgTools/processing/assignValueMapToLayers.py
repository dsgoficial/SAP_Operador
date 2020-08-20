from Ferramentas_Producao.modules.dsgTools.processing.processing import Processing
from qgis import core, gui
import processing
import json

class AssignValueMapToLayers(Processing):
    
    def __init__(self, mediator):
        super(AssignValueMapToLayers, self).__init__()
        self.processingId = 'dsgtools:assignvaluemaptolayersalgorithm'
   
    def getParameters(self, parameters):
        uris = []
        for layerId in parameters['layerIds']:
            uri = self.getLayerUriFromId(layerId)
            if not uri:
                continue
            uris.append(uri)
        return { 
                'VALUE_MAP_FILE' : '.json',
                'VALUE_MAP' : json.dumps(parameters['valueMaps']),
                'INPUT_LAYERS': uris
            }
from Ferramentas_Producao.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class AssignExpressionFieldToLayers(Processing):
    
    def __init__(self, mediator):
        super(AssignExpressionFieldToLayers, self).__init__()
        self.processingId = 'dsgtools:assignexpressionfieldtolayersalgorithm'

    def getParameters(self, parameters):
        uris = []
        for layerId in parameters['layerIds']:
            uri = self.getLayerUriFromId(layerId)
            if not uri:
                continue
            uris.append(uri)
        return {
                'FILE': '.json',
                'TEXT': json.dumps(parameters['expressions']),
                'INPUT_LAYERS' : uris
            }
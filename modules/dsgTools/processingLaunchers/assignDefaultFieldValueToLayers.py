from SAP_Operador.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class AssignDefaultFieldValueToLayers(Processing):
    
    def __init__(self, controller):
        super(AssignDefaultFieldValueToLayers, self).__init__()
        self.processingId = 'dsgtools:assigndefaultfieldvaluetolayersalgorithm'
    
    def getParameters(self, parameters):
        uris = []
        for layerId in parameters['layerIds']:
            uri = self.getLayerUriFromId(layerId)
            if not uri:
                continue
            uris.append(uri)
        return {
                'FILE': '.json',
                'TEXT': json.dumps(parameters['defaultValues']),
                'INPUT_LAYERS' : uris
            }
from SAP_Operador.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class AssignAliasesToLayers(Processing):
    
    def __init__(self, controller):
        super(AssignAliasesToLayers, self).__init__()
        self.processingId = 'dsgtools:assignaliasestolayersalgorithm'
    
    def getParameters(self, parameters):
        uris = []
        for layerId in parameters['layerIds']:
            uri = self.getLayerUriFromId(layerId)
            if not uri:
                continue
            uris.append(uri)
        return {
                'FILE': '.json',
                'TEXT': parameters['aliases'],
                'INPUT_LAYERS' : uris
            }
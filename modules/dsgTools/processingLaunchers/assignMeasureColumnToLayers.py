from Ferramentas_Producao.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class AssignMeasureColumnToLayers(Processing):
    
    def __init__(self, controller):
        super(AssignMeasureColumnToLayers, self).__init__()
        self.processingId = 'dsgtools:assignmeasurecolumntolayers'
    
    def getParameters(self, parameters):
        uris = []
        for layerId in parameters['layerIds']:
            uri = self.getLayerUriFromId(layerId)
            if not uri:
                continue
            uris.append(uri)
        return {
            'INPUT_LAYERS' : uris
        }
from Ferramentas_Producao.modules.dsgTools.processing.processing import Processing
from qgis import core, gui
import processing
import json

class MatchAndApplyQmlStylesToLayers(Processing):
    
    def __init__(self, mediator):
        super(MatchAndApplyQmlStylesToLayers, self).__init__()
        self.processingId = 'dsgtools:matchandapplyqmlstylestolayersalgorithm'

    def getParameters(self, parameters):
        uris = []
        for layerId in parameters['layerIds']:
            uri = self.getLayerUriFromId(layerId)
            if not uri:
                continue
            uris.append(uri)            
        return { 
            'QML_MAP' : json.dumps(parameters['layersQml']),
            'QML_FOLDER' : '/path/to/qmlFolder', 
            'INPUT_LAYERS': uris
        }
            
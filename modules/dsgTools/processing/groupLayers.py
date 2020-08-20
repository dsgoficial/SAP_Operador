from Ferramentas_Producao.modules.dsgTools.processing.processing import Processing
from qgis import core, gui
import processing

class GroupLayers(Processing):
    
    def __init__(self, mediator):
        super(GroupLayers, self).__init__()
        self.processingId = 'dsgtools:grouplayers'

    def getParameters(self, parameters):
        uris = []
        for layerId in parameters['layerIds']:
            uri = self.getLayerUriFromId(layerId)
            if not uri:
                continue
            uris.append(uri)
        return { 
                'CATEGORY_EXPRESSION' : 'substr(@layer_name, 0, strpos(@layer_name, \'_\')-1)', 
                'INPUT_LAYERS' : uris
            }
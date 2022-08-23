from Ferramentas_Producao.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing

class SetRemoveDuplicateNodePropertyOnLayers(Processing):
    
    def __init__(self, controller):
        super(SetRemoveDuplicateNodePropertyOnLayers, self).__init__()
        self.processingId = 'dsgtools:setremoveduplicatenodepropertyonlayers'

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
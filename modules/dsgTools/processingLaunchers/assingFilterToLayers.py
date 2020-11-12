from Ferramentas_Producao.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing

class AssingFilterToLayers(Processing):
    
    def __init__(self, controller):
        super(AssingFilterToLayers, self).__init__()
        self.processingId = 'dsgtools:assignfiltertolayers'

    def run(self, parameters):
        if not self.isAvailable():
            raise Exception("Processamento '{0}' não está disponível".format(self.processingId))
            return
        for layerData in parameters['layers']:
            uri = self.getLayerUriFromTable(layerData['schema'], layerData['nome'])
            if not uri:
                continue
            processing.run(
                self.processingId, 
                self.getParameters({'uri': uri, 'filter': layerData['filter']})
            )
        
    def getParameters(self, parameters):
        return { 
            'BEHAVIOR' : 2, 
            'FILTER' : parameters['filter'], 
            'INPUT_LAYERS' : [ parameters['uri'] ]
        }
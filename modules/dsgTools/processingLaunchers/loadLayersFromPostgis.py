from SAP_Operador.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing

class LoadLayersFromPostgis(Processing):
    
    def __init__(self, controller):
        super(LoadLayersFromPostgis, self).__init__()
        self.processingId = 'dsgtools:loadlayersfrompostgisalgorithm'

    def getParameters(self, parameters):
        return { 
            'DATABASE' : parameters['dbName'], 
            'HOST' : parameters['dbHost'], 
            'LAYER_LIST' : ','.join(parameters['layerNames']), 
            'LOAD_TO_CANVAS' : True, 
            'PASSWORD' : parameters['dbPassword'], 
            'PORT' : parameters['dbPort'], 
            'UNIQUE_LOAD' : True, 
            'USER' : parameters['dbUser']
        }
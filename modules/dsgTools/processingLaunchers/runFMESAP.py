from Ferramentas_Producao.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class RunFMESAP(Processing):
    
    def __init__(self, controller):
        super(RunFMESAP, self).__init__()
        self.processingId = 'dsgtools:runremotefme'
        
    def getParameters(self, parameters):
        return { 
            'FME_MANAGER' : {
                'auth': None, 
                'parameters': {
                    'parametros': {
                        'dbarea_where_clause': "'{}'".format(parameters['workUnitGeometry']), 
                        'dbhost_HOST_POSTGIS': parameters['dbHost'], 
                        'dbname_SourceDataset_POSTGIS': parameters['dbName'], 
                        'dbport_PORT_POSTGIS': parameters['dbPort']
                    }
                }, 
                'proxy_dict': None, 
                'server': parameters['fmeRoutine']['server'], 
                'use_proxy': False, 
                'use_ssl': False, 
                'version': 'v2', 
                'workspace_id': parameters['fmeRoutine']['id']
            } 
        }

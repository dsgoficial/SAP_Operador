from SAP_Operador.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class RunFMESAP(Processing):
    
    def __init__(self, controller):
        super(RunFMESAP, self).__init__()
        self.processingId = 'dsgtools:runremotefme'
        
    def getParameters(self, parameters):
        fmeParameters = {}
        for parameter in parameters['fmeRoutine']['parameters']:
            if 'dbarea' in parameter:
                fmeParameters[parameter] = "'{}'".format(parameters['workUnitGeometry'])
            elif 'dbname' in parameter:
                fmeParameters[parameter] = parameters['dbName']
            elif 'dbport' in parameter:
                fmeParameters[parameter] = parameters['dbPort']
            elif 'dbhost' in parameter:
                fmeParameters[parameter] = parameters['dbHost']
            elif 'dbuser' in parameter:
                fmeParameters[parameter] = parameters['dbUser']
            elif 'dbpassword' in parameter:
                fmeParameters[parameter] = parameters['dbPassword']
            elif 'sapsubfase' in parameter:
                fmeParameters[parameter] = parameters['sapSubfase']
            else:
                fmeParameters[parameter] = ''
        return { 
            'FME_MANAGER' : {
                'auth': None, 
                'parameters': {
                    'parametros': fmeParameters
                }, 
                'proxy_dict': None, 
                'server': parameters['fmeRoutine']['server'], 
                'use_proxy': False, 
                'use_ssl': False, 
                'version': 'v2', 
                'workspace_id': parameters['fmeRoutine']['id']
            } 
        }

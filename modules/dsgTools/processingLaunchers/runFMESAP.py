from Ferramentas_Producao.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class RunFMESAP(Processing):
    
    def __init__(self, controller):
        super(RunFMESAP, self).__init__()
        self.processingId = 'dsgtools:runfmesap'
        
    def getParameters(self, parameters):
        fmeJSON = {}
        for parameter in parameters['fmeRoutine']['parameters']:
            if 'dbarea' in parameter:
                fmeJSON[parameter] = "'{0}'".format(parameters['workUnitGeometry'])
            elif 'dbname' in parameter:
                fmeJSON[parameter] = parameters['dbName']
            elif 'dbport' in parameter:
                fmeJSON[parameter] = parameters['dbPort']
            elif 'dbhost' in parameter:
                fmeJSON[parameter] = parameters['dbHost']
            else:
                fmeJSON[parameter] = ''
        fmeJSON['server'] = parameters['fmeRoutine']['server']
        fmeJSON['workspace_id'] = parameters['fmeRoutine']['workspace_id']
        return {
            'FILE' : '.json', 
            'TEXT' : json.dumps(fmeJSON) 
        }
from SAP_Operador.modules.dsgTools.processingLaunchers.processing import Processing
from qgis import core, gui
import processing
import json

class RuleStatistics(Processing):

    def __init__(self, controller):
        super(RuleStatistics, self).__init__()
        self.processingId = 'dsgtools:rulestatistics'

    def run(self, parameters):
        proc = super().run(parameters)
        if 'OUTPUT' in proc and proc['OUTPUT']:
            result = {}
            currentRuleKey = None
            for line in proc['OUTPUT'].split('\n\n'):
                if ('[regras]' in line.lower() or '[rules]' in line.lower()) and not(line in result):
                    currentRuleKey = line
                    result[line] = []
                elif 'passaram' in line.lower():
                    continue
                elif currentRuleKey and line:
                    result[currentRuleKey].append(line)
            return result
        return None

    def getParameters(self, parameters):
        layers = [self.getLayerUriFromTable(layerData['schema'], layerData['nome']) for layerData in parameters['layers']]
        layers = [l for l in layers if l is not None]
        return {
            'INPUTLAYERS' : layers,
            'RULEFILE' : '.json',
            'RULEDATA' : parameters['rules'],
            'FLAGS': 'memory:',
            'UNUSUAL_ATTRIBUTES': 'memory:',
        }

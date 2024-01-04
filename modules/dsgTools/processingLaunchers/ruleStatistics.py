from Ferramentas_Producao.modules.dsgTools.processingLaunchers.processing import Processing
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
                if '[regras]' in line.lower() and not(line in result):
                    # html+='<h3>{0}</h3>'.format(line)
                    currentRuleKey = line
                    result[line] = []
                elif 'passaram' in line.lower():
                    continue
                #     html += u"<p style=\"color:green\">{0}</p>".format(line)
                elif currentRuleKey and line:
                    # html += u"<p style=\"color:red\">{0}</p>".format(line)
                    result[currentRuleKey].append(line)
            return result
        # return "<p style=\"color:red\">{0}</p>".format(
        #     'Não há regras para as camadas carregadas!'
        # )
        return None
        
    def getParameters(self, parameters):
        layers = [self.getLayerUriFromTable(layerData['schema'], layerData['nome']) for layerData in parameters['layers']]
        layers = [l for l in layers if l is not None]
        return { 
            'INPUTLAYERS' : layers,
            'RULEFILE' : '.json', 
            'RULEDATA' : parameters['rules']
        }
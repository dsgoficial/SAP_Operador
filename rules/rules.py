# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui

class Rules(QtCore.QObject):
    def __init__(self, iface):
        #Construtor
        super(Rules, self).__init__()
        self.iface = iface
        self.rulesToTable = None
        self.rulesToForm = None
      
    def preFormattingStatisticRules(self, data):
        #Método para pré formatar o dicionário que receberá os dados
        #dos testes das regras
        statisticRules = data['statisticRules']
        layerLoaded = [lyr.name() for lyr in data['treeLayers'] ]
        for ruleNameType in statisticRules:
            for i in data['rules']:
                if ruleNameType == data['rules'][i]['tipo_estilo']:
                    layerName = data['rules'][i]['camada']
                    if layerName in layerLoaded:
                        if not(layerName in statisticRules[ruleNameType]):
                            statisticRules[ruleNameType][layerName] = {
                                'allRules' : [],
                                'okRules' : 0,
                            }
                        statisticRules[ruleNameType][layerName]\
                                      ['allRules'].append(
                            data['rules'][i]['regra']
                        )
        return statisticRules

    def checkRulesOnLayers(self, statisticRules, treeLayers):
        #Método para executar os testes das regras
        for ruleNameType in statisticRules:
            for tlyr in treeLayers:
                testLayer =(tlyr and ( tlyr.layer().name() in statisticRules\
                                                                [ruleNameType]))
                if testLayer:
                    vlayer = tlyr.layer()
                    layerName = tlyr.layer().name()
                    rules = statisticRules[ruleNameType]\
                                          [layerName]['allRules']
                    for rule in rules:
                        vlayer.selectByExpression(rule)
                        count = vlayer.selectedFeatureCount()
                        vlayer.removeSelection()
                        if count == 0:
                             statisticRules[ruleNameType][layerName]\
                                                         ['okRules']+=1
        

    def formatOutputStatisticRules(self, statisticRules):
        #Método para formata os dados do dicionário das regras em um html
        html=""
        for ruleName in sorted(statisticRules):
            row = U"<h1>[REGRAS] : {0}</h1>".format(ruleName)
            html += row
            layersRecused = []
            for layerName in sorted(statisticRules[ruleName]):
                    countAllRules = len(statisticRules[ruleName]\
                                         [layerName]['allRules'])
                    countOkRules = statisticRules[ruleName]\
                                     [layerName]['okRules']
                    layersRecused.append(layerName) if (countOkRules/countAllRules) != 1 else 0
            rows = ""
            if len(layersRecused) != 0:
                for name in layersRecused:
                    rows += u"<p style=\"color:red\">{0}</p>".format(name)
            else:
                rows = u"<p style=\"color:green\">{0}</p>".format(
                    "As camadas passaram em todas as regras."
                )
            html += rows
        return html

    def getStatisticRules(self, rulesSelected, workspaceName): 
        #Método que retorna um html com a estatísticas das regras
        root = core.QgsProject.instance().layerTreeRoot()
        groupDb = root.findGroup(workspaceName)
        if groupDb:
            treeLayers = groupDb.findLayers()
            rules = self.rulesData
            rulesTypeSelected = rulesSelected
            statisticRules = { item : {} for item in rulesTypeSelected} 
            statisticRulesPreFormated = self.preFormattingStatisticRules({
                'statisticRules' : statisticRules,
                'rules' : rules,
                'treeLayers' : treeLayers,
            })
            self.checkRulesOnLayers(statisticRulesPreFormated, treeLayers)
            return self.formatOutputStatisticRules(statisticRulesPreFormated)
                          
    def loadRuleOnlayer(self, data):
        #Método para carrega as regras selectionada nas camadas
        vlayer = data['vectorLayer']
        layerName = vlayer.name()
        selectedRulesType = data['selectedRulesType']
        conditionalStyleRules = self.conditionalStyleRules
        rules = {}
        selectedRuleOnOrder = { conditionalStyleRules["order_rules"][k.encode("utf-8")] : k.encode("utf-8")  for k in selectedRulesType}
        for order in reversed(sorted(selectedRuleOnOrder)):
            selectedRule = selectedRuleOnOrder[order]
            for ruleType in conditionalStyleRules[selectedRule]:
                if not(ruleType in rules):
                    rules[ruleType] = {}
                if layerName in conditionalStyleRules[selectedRule][ruleType]:
                    for field in conditionalStyleRules[selectedRule]\
                                               [ruleType][layerName]:
                                if not(field in rules[ruleType]):
                                    rules[ruleType][field] = []
                                rules[ruleType][field]+=conditionalStyleRules\
                                                                [selectedRule]\
                                                        [ruleType][layerName][field]
        self.addRuleOnLayer({
                        'vectorLayer' : vlayer,
                        'allRulesOfLayer': rules,
                    })                    
        
    def addRuleOnLayer(self, data):
        #Método que adiciona a regra na camada
        rules = data['allRulesOfLayer']
        vlayer = data['vectorLayer']
        for ruleType in rules:
            for field in rules[ruleType]:
                if ruleType  == 'Atributo':
                    vlayer.conditionalStyles()\
                        .setFieldStyles( field, rules[ruleType][field])
                else:
                    vlayer.conditionalStyles()\
                        .setRowStyles(rules[ruleType][field])

    def formatRulesToForm(self):
        rulesData = self.rulesData 
        rulesToForm = {}
        rulesToForm["order_rules"] = {}
        for i in rulesData:
            styleType = rulesData[i]['tipo_estilo'].encode("utf-8")
            ruleType = rulesData[i]['tipo_regra'].decode("utf-8")
            ruleCamada = rulesData[i]['camada'].decode("utf-8")
            cor_rgb = rulesData[i]['cor_rgb'].decode("utf-8")
            field = rulesData[i]['atributo'].decode("utf-8")
            description = rulesData[i]['descricao']
            rule = rulesData[i]['regra']
            order = rulesData[i]['ordem']
            if not order in rulesToForm:
                rulesToForm["order_rules"][styleType] = order
            if not styleType in rulesToForm:
                rulesToForm[styleType] = {}
            if not ruleCamada in rulesToForm[styleType]:
                rulesToForm[styleType][ruleCamada] = {}
            if not field in rulesToForm[styleType][ruleCamada]:
                rulesToForm[styleType][ruleCamada][field] = []
            rulesToForm[styleType][ruleCamada][field].append({
                'rule' : rule,
                'cor_rgb' : cor_rgb,
                'descricao' : description
            })
        self.rulesToForm = rulesToForm

    def formatRulesToConditionalStyle(self):
        rulesData = self.rulesData
        rules = {}
        rules["order_rules"] = {}
        for i in rulesData:
            styleType = rulesData[i]['tipo_estilo'].encode("utf-8")
            ruleType = rulesData[i]['tipo_regra'].decode("utf-8")
            ruleCamada = rulesData[i]['camada'].decode("utf-8")
            cor_rgb = rulesData[i]['cor_rgb'].decode("utf-8")
            field = rulesData[i]['atributo'].decode("utf-8")
            description = rulesData[i]['descricao']
            rule = rulesData[i]['regra']
            order = rulesData[i]['ordem']
            if not order in rules:
                rules["order_rules"][styleType] = order
            if not styleType in rules:
                rules[styleType] = {}
            if not ruleType in rules[styleType]:
                rules[styleType][ruleType] = {}
            if not ruleCamada in rules[styleType][ruleType]:
                rules[styleType][ruleType][ruleCamada] = {}
            if not field in rules[styleType][ruleType][ruleCamada]:
                rules[styleType][ruleType][ruleCamada][field] = []
            conditionalStyle = self.createConditionalStyle(rulesData[i])
            rules[styleType][ruleType][ruleCamada][field].append(conditionalStyle)
        self.conditionalStyleRules = rules 

    def formatRulesToCaseExpression(self):
        rulesData = self.rulesData
        rulesToCase = {} 
        for i in rulesData:
            styleType = rulesData[i]['tipo_estilo'].encode("utf-8")
            ruleType = rulesData[i]['tipo_regra'].decode("utf-8")
            ruleCamada = rulesData[i]['camada'].decode("utf-8")
            cor_rgb = rulesData[i]['cor_rgb'].decode("utf-8")
            field = rulesData[i]['atributo'].decode("utf-8")
            description = rulesData[i]['descricao']
            rule = rulesData[i]['regra']
            if not styleType in rulesToCase:
                rulesToCase[styleType] = {}
            if not ruleCamada in rulesToCase[styleType]:
                rulesToCase[styleType][ruleCamada] = {}
            if not field in rulesToCase[styleType][ruleCamada]:
                rulesToCase[styleType][ruleCamada][field] = []
            rulesToCase[styleType][ruleCamada][field].append({
                'rule' : rule,
                'description' : description,
            })
        self.rulesToTable = rulesToCase
    
    def createRules(self, rulesData):
        #Método que formata todas as regras em um dicionário
        self.rulesData =  rulesData
        self.formatRulesToCaseExpression()
        self.formatRulesToConditionalStyle()
        self.formatRulesToForm()        

    def createConditionalStyle(self, data):
        #Método que cria a regra
        conditionalStyle = core.QgsConditionalStyle()
        conditionalStyle.setName( data['descricao'] )
        conditionalStyle.setRule( data['regra'] )
        conditionalStyle.setBackgroundColor(
            QtGui.QColor(
                data['corRgb'][0],
                data['corRgb'][1],
                data['corRgb'][2]
            ) 
        )
        return conditionalStyle
        
    def cleanRules(self, groupDbName):
        #Método que limpa as regras de todas as camadas
        root = core.QgsProject.instance().layerTreeRoot()
        groupDb = root.findGroup(groupDbName)
        if groupDb:
            for treeLayer in groupDb.findLayers():
                lyr = treeLayer.layer()
                if lyr.type() == core.QgsMapLayer.VectorLayer:
                    for idxField in lyr.attributeList():
                        fieldName = lyr.pendingFields().field(idxField).name()
                        lyr.conditionalStyles().setFieldStyles(fieldName, '')





import concurrent.futures
import os
import json

class Filters:
    
    def filterCommonFields(self, selectedLayers):
        commonFields = []
        if len(selectedLayers) == 1:
            return [
                [n, 1]
                for n in selectedLayers[0].fields().names()
            ]
        else:
            fieldLists = []
            for l in selectedLayers:
                fieldNames = l.fields().names()
                fieldLists.append(fieldNames)
            commonFields = list(set(fieldLists[0]).intersection(*fieldLists[1:]))  
            return [ [n] for n in commonFields]

    def filterAttributeCombination(self, selectedFields, selectedLayers):
        attributeLists = []
        def readAttributes(f):
            values = []
            for fieldName in selectedFields:
                fieldConfig = f.fields().field(f.fields().indexOf(fieldName)).editorWidgetSetup().config()
                if 'map' in fieldConfig:
                    inv_map = {v: k for k, v in fieldConfig['map'].items()}
                    values.append(inv_map[f[fieldName]])
                    continue
                values.append(f[fieldName])
            attributeLists.append(values)
        
        pool = concurrent.futures.ThreadPoolExecutor(os.cpu_count()-1)
        futures = set()
        for layer in selectedLayers:
            features = list(layer.getFeatures())
            for feature in features:
                futures.add(pool.submit(readAttributes, feature))
        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.ALL_COMPLETED)
        attributeCountMap = {
            ','.join([str(n) for n in attributes]): attributeLists.count(attributes) 
            for attributes in attributeLists
        }
        rows = []
        for key in attributeCountMap:
            displayValues = []
            dump = {}
            attributes = key.split(',')
            for idx, attribute in enumerate(attributes):
                dump[selectedFields[idx]] = attribute
                displayValues.append('{} ({})'.format(attribute, selectedFields[idx]))
            rows.append(
                [
                    ';\n'.join(displayValues),
                    attributeCountMap[key],
                    json.dumps(dump)
                ]
            )
        return rows

    def getLayersByAttributes(self, attributeLists, selectedLayers):
        rows = []
        for layer in selectedLayers:
            for attributes in attributeLists:
                layer.removeSelection()
                expression = self.createExpression(layer.fields(), attributes)
                if not expression:
                    continue
                layer.selectByExpression(expression)
                count = layer.selectedFeatureCount()
                case = ';\n'.join([ '{} ({})'.format(attributes[k], k) for k in attributes ])
                rows.append([case, layer.name(), count])
        return rows

    def createExpression(self, qgsFields, fields):        
        expressions = []
        for n in fields:
            fieldIndex = qgsFields.indexOf(n)
            if fieldIndex < 0:
                return
            fieldConfig = qgsFields.field(fieldIndex).editorWidgetSetup().config()
            if 'map' in fieldConfig and not(fields[n] in fieldConfig['map']):
                return
            elif 'map' in fieldConfig:
                value = fieldConfig['map'][fields[n]]
            else:
                value = fields[n]
            expressions.append(
                '"{}" is {}'.format(
                    n,
                    self.formatValue(value) 
                )
            )
        return ' AND '.join(expressions) 

    def formatValue(self, value):
        if self.isNumber(value):
            return value
        if value == 'NULL':
            return value
        return "'{}'".format(value)

    def isNumber(self, value):
        for t in [int, float]:
            try:
                t(value)
            except:
                return False
        return True
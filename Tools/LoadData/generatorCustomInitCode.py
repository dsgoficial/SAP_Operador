#! -*- coding: utf-8 -*-
import json
import os

class GeneratorCustomInitCode(object):
    def __init__(self):
        # contrutor
        super(GeneratorCustomInitCode, self).__init__() 

    def getInitCodeWithFilter(self, tableFilter, rules):
        optFilter = self.formatOptionFilter(tableFilter)
        tableFilterFormated = self.formatTableFilter(tableFilter)
        initCode = self.getTemplateInitCodeWithFilter()
        initCode = initCode.replace(
            '{optfilter}', 
            json.dumps(optFilter, ensure_ascii=False)
        )
        initCode = initCode.replace(
            '{filter}', 
            json.dumps(tableFilterFormated, ensure_ascii=False)
        )
        initCode = initCode.replace(
            '{rules}', 
            json.dumps(rules, ensure_ascii=False)
        )
        return initCode

    def getInitCodeWithoutFilter(self, rules):
        initCode = self.getTemplateInitCodeNotFilter()
        initCode = initCode.replace(
            '{rules}', 
            json.dumps(rules, ensure_ascii=False)
        )
        return initCode

    def formatTableFilter(self, tableFilter):
        tableFilterFormated = {}
        for line in tableFilter:
            tableFilterFormated[line[1]] = line[0]
        return tableFilterFormated
    
    def formatOptionFilter(self, tableFilter):
        optFilter = {}
        for line in tableFilter:
            optFilter[unicode(line[2])] = ((line[0]-(line[0]%100))/100)
        return optFilter

    def getTemplateInitCodeNotFilter(self):
        initCodeTemplate = u""
        pathCode = os.path.join(
            os.path.dirname(__file__),
            'formInitCodeWithoutFilterTemplate.txt'
        )
        codeFile = open(pathCode, "r")
        for line in codeFile.readlines():
            initCodeTemplate += line#.decode("utf-8")
        codeFile.close()
        return initCodeTemplate

    def getTemplateInitCodeWithFilter(self):
        initCodeTemplate = u""
        pathCode = os.path.join(
            os.path.dirname(__file__),
            'formInitCodeWithFilterTemplate.txt'
        )
        codeFile = open(pathCode, "r")
        for line in codeFile.readlines():
            initCodeTemplate += line#.decode("utf-8")
        codeFile.close()
        return initCodeTemplate
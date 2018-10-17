# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui
from generatorCustomForm import GeneratorCustomForm
from generatorCustomInitCode import GeneratorCustomInitCode
import os, json, sys, platform, copy
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from managerQgis.projectQgis import ProjectQgis

class LoadLayers(QtCore.QObject):

    updateProgressBar = QtCore.pyqtSignal()
    
    def __init__(self, iface, loginData):
        super(LoadLayers, self).__init__()
        self.iface = iface
        self.filters = {}
        self.filterSelected = None
        self.rules = {}
        self.loginData = loginData
            
    def reloadFormsCustom(self):
        for vlayer in core.QgsMapLayerRegistry.instance().mapLayers().values():
            data = core.QgsExpressionContextUtils.layerScope(vlayer).variable(u"uiData")
            if data and vlayer.type() == core.QgsMapLayer.VectorLayer:
                uiData = json.loads(
                    data
                )
                customForm = GeneratorCustomForm()
                customForm.create(
                    self.newUiForm(uiData[u"formName"]), 
                    uiData[u"layerData"], 
                    uiData[u"fieldsSorted"],
                    vlayer
                )    

    def cleanDirectoryUI(self):
        directoryPath = os.path.join(
            os.path.dirname(__file__),
            u"formsCustom"
        )
        filelist = [ f for f in os.listdir(directoryPath)]
        for f in filelist:
            if not('.py' in f):
                os.remove(os.path.join(directoryPath, f))
        
    def setFilters(self, d):
        self.filters = d 

    def getFilters(self):
        return self.filters

    def setFilterSelected(self, d):
        self.filterSelected = d 

    def getFilterSelected(self):
        return self.filterSelected
   
    def createConnection(self, data):
        host = data[u"host"]
        dbname = data[u"dbname"]
        user = data[u"user"]
        passwd = data[u"password"]
        port = data[u"port"]
        return host, port, dbname, user, passwd

    def loadRasterLayer(self, path, originalName, newName):
        pathFile = path
        if platform.system() == u"Linux":
            pathFile = path.replace(u"\\", u"/")
        layer = core.QgsRasterLayer(u"{0}/{1}".format(pathFile, originalName), newName)
        if layer.isValid():
            core.QgsMapLayerRegistry.instance().addMapLayer(layer)
            return True
       
    def loadAllLayersSelected(self, userData):
        aliasdb = userData[u'dbAlias']
        layersSelected = userData[u'layersSelected']
        layersSelectedFormated = userData[u'layersSelectedFormated']
        jsonDb = userData[u'dbJson']
        host, port, dbname, user, passwd = self.createConnection(
            jsonDb[u'dataConnection']
        )
        
        if self.loginData:
            groupDbName = userData[u'workspace']
            groupDb = self.addGroupDb(groupDbName)
        else:
            groupDbName = aliasdb+"-"+userData['workspace']
            groupDb = self.addGroupDb(groupDbName)
        self.rules.cleanRules(groupDbName) if self.rules else ""
        for nameGeom in reversed(sorted(layersSelectedFormated)):
            for nameCatLayer in sorted(layersSelectedFormated[nameGeom]):
                for layerName in sorted(layersSelectedFormated[nameGeom][nameCatLayer]):
                    data = {
                        u'layerName' : layerName,
                        u'dbAlias' : aliasdb,
                        u'nameGeom' : nameGeom,
                        u'nameCatLayer' : nameCatLayer,
                        u'styles' : jsonDb[u'styles'],
                        u'workspaces' : jsonDb[u'workspaces'],
                        u'groupDb' : groupDb,
                        u'workspaceName' : userData['workspace'], 
                        u'userData' : userData,
                        u'host' : host,
                        u'port' : port,
                        u'dbname' : dbname,
                        u'user' : user,
                        u'fieldsData' : jsonDb[dbname][nameGeom][nameCatLayer][layerName],
                        u'passwd' : passwd,
                        u'selectedRulesType' : userData[u'selectedRulesType'],
                        u'only_geom' : userData[u'only_geom'] if userData.has_key(u'only_geom') else False           
                    }
                    data[u'groupGeom'] = self.addGroupGeom(data)
                    data[u'groupLayer'] = self.addGroupLayer(data)
                    self.addLayer(data)
                    if userData[u'activeProgressBar']:
                        self.updateProgressBar.emit()
        self.createTmpMoldura(data)
        self.collapseAllTree(groupDbName)

    def createTmpMoldura(self, data):
        if self.loginData:
            srid = self.loginData["dados"]["atividade"]["geom"].split(";")[0].split("=")[1]
            wkt = self.loginData["dados"]["atividade"]["geom"].split(";")[1]
            temp = core.QgsVectorLayer("?query=SELECT geom_from_wkt('%s') as geometry&geometry=geometry:3:%s"%(wkt, srid), "moldura", "virtual")
            qml_path = os.path.join(
                os.path.dirname(__file__),
                'stylesQml',
                'estilo_moldura.qml'
            )
            temp.loadNamedStyle(qml_path)
            group = data["groupDb"].addGroup("layersTmp")
            layerTmp = core.QgsMapLayerRegistry.instance().addMapLayer(temp, False)
            group.addLayer(layerTmp)
        
    def collapseAllTree(self, groupName):
        root = core.QgsProject.instance().layerTreeRoot()
        g1 = root.findGroup(groupName)
        g1.setExpanded(False)
        for g2 in g1.children():
            g2.setExpanded(False)
            for g3 in g2.children():
                g3.setExpanded(False)
                for g4 in g3.children():
                    g4.setExpanded(False)
                                     
    def addGroupDb(self, groupName ):
        # adiciona grupo do banco ou retorna existente
        root = core.QgsProject.instance().layerTreeRoot()
        result = root.findGroup(groupName)
        if result:
            return result
        else:
            newGroup = root.addGroup(groupName)
            return newGroup     

    def addGroupGeom(self, data):
        # adiciona grupo de geometria ou retorna existente
        nameGeom = data[u'nameGeom']
        groupDb = data[u'groupDb']
        result = groupDb.findGroup(nameGeom)
        if result:
            return result
        else:
            groupGeom = groupDb.addGroup(nameGeom)
            return groupGeom

    def addGroupLayer(self, data):
        # adiciona grupo de camada ou retorna existente
        nameCatLayer = data[u'nameCatLayer']
        groupGeom = data[u'groupGeom']
        result = groupGeom.findGroup(nameCatLayer)
        if result:
            return result
        else:
            groupCatLayer = groupGeom.addGroup(nameCatLayer)
            return groupCatLayer

    def getExtraFilter(self, layerName):
        filterData = self.filters
        filterType = self.filterSelected
        extraFilter = ''
        for x in filterData:
            if filterType == filterData[x][u'tipo_filtro'] and layerName == filterData[x][u'camada']:
                extraFilter+=u'AND {0}'.format(filterData[x][u'filtro'])
        return extraFilter


    def getFilterWhere(self, workspace, layerName, workspaceName):
        extraFilter = self.getExtraFilter(layerName)
        if layerName == u'aux_moldura_a':
            filterWhere = ' '.join([u'''"mi" = \'%s\''''%(workspaceName), extraFilter]) 
        else: 
            filterWhere = ' '.join([u'''st_intersects(geom, st_geomfromewkt('%s'))'''%(workspace), extraFilter])
        return filterWhere

    def getClausuleWhereAndWorkspace(self, data):
        workspaceName = data[u'workspaceName']
        if workspaceName != u'Todas as unidades':
            if self.loginData:
                workspace = self.loginData["dados"]["atividade"]["geom"]
            else:
                workspace = data[u'workspaces'][data[u'workspaceName']]
            #ProjectQgis(self.iface).setProjectVariable('moldura_ewkt', workspace)
            where = self.getFilterWhere(workspace, data['layerName'], workspaceName)
            return where, workspace
        return '', ''

    def getURIString(self, data, where):
        layerName = data['layerName']
        return u'''dbname=\'{0}\' host={1} port={2} \
            user=\'{3}\' password=\'{4}\' table="{7}"."{5}" (geom) sql={6}'''\
            .format(data['dbname'], data['host'], data['port'], 
            data['user'], data['passwd'], layerName, where, data[u'fieldsData']['schema'])

    def getLayer(self, data):
        layerName = data[u'layerName']
        groupLayer = data[u'groupLayer']
        layers = groupLayer.findLayers()
        for l in layers:
            if l and layerName == l.layer().name():
                return l.layer()
        return False

    def addLayer(self, data):
        layerName = data[u'layerName']
        where, workspace = self.getClausuleWhereAndWorkspace(data)        
        vlayer = self.getLayer(data)  
        if vlayer:
            vlayer.setSubsetString(where)
        else:
            uriString = self.getURIString(data, where)
            vlayer = core.QgsVectorLayer(uriString, layerName, u"postgres")
        data[u'vectorLayer'] = vlayer
        data[u'workspaceData'] = workspace
        groupLayer = data[u'groupLayer']
        if vlayer and data['only_geom'] and vlayer.allFeatureIds():
            vl = core.QgsMapLayerRegistry.instance().addMapLayer(vlayer, False)
            groupLayer.addLayer(vl)
            self.loadLayer(data)
        elif vlayer and not(data['only_geom']):
            vl = core.QgsMapLayerRegistry.instance().addMapLayer(vlayer, False)
            groupLayer.addLayer(vl)
            self.loadLayer(data)

    def loadLayer(self, data):   
        self.loadStyleOnLayer(data)
        self.loadValueMap(data)
        self.addDefaultValues(data)
        self.loadFormCustom(data)
        self.addFieldGeom(data)
        self.addVariablesOnLayer(data)
        self.addRule(data)

    def addDefaultValues(self, data):
        if self.loginData:
            vl = data[u'vectorLayer']
            idx = vl.fieldNameIndex( 'ultimo_usuario' )
            if idx > 0:
                vl.setDefaultValueExpression(idx, "'{0}'".format(self.loginData['dados']['usuario_id']))

    def loadValueMap(self, data):
        vlayer = data[u'vectorLayer']
        fieldsData = data[u'fieldsData']
        fields = self.getFieldsName(vlayer)
        for fieldName in fields:
            fieldIndex = vlayer.fieldNameIndex( fieldName )
            isValueMap = (
                (fieldIndex > 0 )and
                (fieldName in  fieldsData) and 
                ( u'ValueMap' in fieldsData[fieldName])
            )
            if isValueMap:
                vlayer.setEditorWidgetV2( fieldIndex, 'ValueMap' )
                values = copy.deepcopy(fieldsData[fieldName][u'ValueMap'])
                if (u'IGNORAR' in values) or (u'Ignorar' in values):
                    del values[u'IGNORAR']
                vlayer.setEditorWidgetV2Config( fieldIndex, values )

    def getFieldsName(self, layer):
        conf = layer.fields()
        fieldIndex = conf.allAttributesList()
        nameField = []
        for i in fieldIndex:
            nameField.append(conf.field(i).name())
        return nameField
                        
    def loadStyleOnLayer(self, data):
        # carrega o estilo escolhido
        style = data[u'userData'][u'styleName']
        if style != u'<Opções>':
            vectorLayer = data[u'vectorLayer']
            vectorLayer.loadDefaultStyle()
            layerName = vectorLayer.name()
            styles = data[u'styles']
            sep = '/' if '/' in styles.keys()[0] else '_'
            loadStyles = [u'{}{}{}'.format(style, sep, layerName)] 
            for styleName in loadStyles:
                if styles and (styleName in styles):
                    idStyle = str(styles[styleName])
                    styleXMl = vectorLayer.getStyleFromDatabase(idStyle, u"Erro")
                    vectorLayer.applyNamedStyle(styleXMl)       
    
    def addFieldGeom(self, data):
        # adiciona campo extra na camada
        vectorLayer = data[u'vectorLayer']
        if vectorLayer.geometryType() == 1:
            vectorLayer.addExpressionField(u'$length',
                core.QgsField(u'length_otf', QtCore.QVariant.Double))
        elif vectorLayer.geometryType() == 2:
            vectorLayer.addExpressionField(u'$area',
                core.QgsField(u'area_otf', QtCore.QVariant.Double))
        caseOfRules = self.getCaseOfRules(data) 
        if caseOfRules:
            vectorLayer.addExpressionField(caseOfRules,
                    core.QgsField(u'descricao_erro', QtCore.QVariant.String))

    def getSelectedRulesToTable(self, data):
        rules = {}
        for ruleName in data['selectedRulesType']: 
            rules[ruleName] = self.rules.rulesToTable[ruleName.encode("utf-8")]
        return rules

    def getTemplateRulesCase(self):
        return u'''CASE {0} ELSE "Sem erros!" END'''

    def getCaseOfRules(self, data):
        rulesSelected = self.getSelectedRulesToTable(data)
        currentLayerName = data[u'layerName']
        ruleCase = self.getTemplateRulesCase()
        cases = ""
        for typeRule in rulesSelected:
            for layerName in rulesSelected[typeRule]:
                if layerName == currentLayerName:
                    for field in rulesSelected[typeRule][layerName]:
                        for exp in rulesSelected[typeRule][layerName][field]:
                            case = u"WHEN {0} THEN {1}\n".format(
                                exp["rule"],
                                u"'{0}'".format(exp["description"])
                            )
                            cases+=case
        ruleCase = ruleCase.replace("{0}", cases) if cases else None
        return ruleCase
                                       		
    def addRule(self, data):
        if data[u'selectedRulesType']:
            self.rules.loadRuleOnlayer({
                u'selectedRulesType' : data[u'selectedRulesType'],
                u'vectorLayer' :  data[u'vectorLayer'],
            })

    def addVariablesOnLayer(self, data):
        vlayer = data[u'vectorLayer']
        workspaceName = data[u'workspaceName']
        workspaceData = data[u'workspaceData']
        core.QgsExpressionContextUtils\
            .setLayerVariable( vlayer, 
                            u'area_trabalho_nome',
                            workspaceName)
        core.QgsExpressionContextUtils\
            .setLayerVariable( vlayer, 
                            u'area_trabalho_poligono',
                            workspaceData)
                
    def sortFieldsLayer(self, fields):
        fieldsSorted = []
        if u'nome' in fields:
            fieldsSorted.append(u'nome')
        if u'filter' in fields:
            fieldsSorted.append(u'filter')
            fieldsSorted.append(u'tipo')
        for field in fields:
            if not(field in fieldsSorted):
                fieldsSorted.append(field)
        return fieldsSorted

    def newUiForm(self, pathUiForm):
        formFile = open(pathUiForm, "w")
        return formFile
        
    def createCustomForm(self, formFile,  data):     
        dbData = data['userData']['dbJson'][data['dbname']]
        layerData = dbData[data['nameGeom']][data['nameCatLayer']][data['layerName']]
        fieldsSorted = self.sortFieldsLayer(layerData.keys())
        customForm = GeneratorCustomForm()
        customForm.create(formFile, layerData, fieldsSorted, data['vectorLayer'])
        vlayer = data['vectorLayer']
        core.QgsExpressionContextUtils.setLayerVariable( 
            vlayer, 
            u'uiData',
            json.dumps({
                'layerData' : layerData, 
                'fieldsSorted' : fieldsSorted,
                'formName' : formFile.name
            }, ensure_ascii=False)
        )
         
    def getPathUiForm(self, data):
        dbName = data['dbname']
        layerName = data['layerName']
        pathUiForm =  os.path.join(
            os.path.dirname(__file__), 
            'formsCustom' ,
            '{0}_{1}.ui'.format(dbName, layerName)
        )
        return pathUiForm
    
    def loadFormCustom(self, data):
        pathUiForm = self.getPathUiForm(data)
        formFile = self.newUiForm(pathUiForm)
        self.createCustomForm(formFile, data)
        data['vectorLayer'].editFormConfig().setInitCodeSource(2)
        data['vectorLayer'].editFormConfig().setLayout(2)
        data['vectorLayer'].editFormConfig().setUiForm(pathUiForm)
        initCode = self.createCustomInitCode(data)
        if initCode:
            data['vectorLayer'].editFormConfig().setInitFunction("formOpen")
            data['vectorLayer'].editFormConfig().setInitCode(initCode)

    def getRulesSelected(self, data):
        rules = []
        currentlayerName = data['layerName']
        if  self.rules:
            allRules = self.rules.rulesToForm
            selectedRuleOnOrder = { allRules["order_rules"][k.encode("utf-8")] : k.encode("utf-8")  for k in data['selectedRulesType']}
            for order in reversed(sorted(selectedRuleOnOrder)):
                ruleName = selectedRuleOnOrder[order]
                for lyrName in  allRules[ruleName]:
                    if  currentlayerName == lyrName:
                        rules.append(allRules[ruleName][currentlayerName])
            return rules
        return {}

    def createCustomInitCode(self, data):
        rules = self.getRulesSelected(data)
        dbData = data['userData']['dbJson'][data['dbname']]
        layerData = dbData[data['nameGeom']][data['nameCatLayer']][data['layerName']]
        if 'filter' in layerData:
            customInitCode = GeneratorCustomInitCode()
            initCode = customInitCode.getInitCodeWithFilter(layerData['filter'], rules)
            return initCode
        else:
            customInitCode = GeneratorCustomInitCode()
            initCode = customInitCode.getInitCodeNotFilter(rules)
            return initCode
          
class SapActivityPostgres:

    def __init__(self):
        self.data = {}

    def setData(self, data):
        self.data = data

    def getData(self):
        return self.data

    def getMenus(self):
        return self.getData()['menus']

    def getLayerGroup(self, layerName):
        return layerName.split('_')[0]

    def getFormRules(self, layerName):
        rules = {}
        for data in self.getRules():
            if not( data['camada'] == layerName):
                continue
            if not(data['ordem'] in rules):
                rules[data['ordem']] = {}
            if not(data['atributo'] in rules[data['ordem']]):
                rules[data['ordem']][data['atributo']] = []
            rules[data['ordem']][data['atributo']].append({
                'rule' : data['regra'],
                'cor_rgb' : data['cor_rgb'],
                'descricao' : data['descricao']
            })
        return [
            rules[order]
            for order in reversed(sorted(rules))
        ]

    def getExpressionField(self, layerName):
        expression = ''
        for data in self.getRules():
            if not( data['camada'] == layerName ):
                continue
            expression += 'WHEN {0} THEN {1}\n'.format(
                data['regra'],
                "'{0}'".format(data['descricao'])
            )
        if not expression:
            return ''
        return '''CASE {0} ELSE "Sem erros!" END'''.format(expression)

    def getConditionalStyles(self, layerName):
        rules = {}
        for data in self.getRules():
            if not( data['camada'] == layerName ):
                continue
            if not(data['ordem'] in rules):
                rules[data['ordem']] = {}
                rules[data['ordem']]['tipo'] = data['tipo_regra']
                rules[data['ordem']]['atributos'] = {}
            if not data['atributo'] in rules[data['ordem']]['atributos']:
                rules[data['ordem']]['atributos'][data['atributo']] = []
            rules[data['ordem']]['atributos'][data['atributo']].append({
                    'descricao' : data['descricao'],
                    'regra' : data['regra'],
                    'corRgb' : data['cor_rgb']
            })
        return rules


    def getConditionalStyleNames(self):
        return [ data['descricao'] for data in self.getRules() ]

    def getLayerNames(self):
        return [ layer['nome'] for layer in self.getLayers()]
            
    def getLayers(self):
        return self.getData()['layers'][:]

    def getWorkspaceNames(self):
        return [ workspace['nome'] for workspace in self.getData()['workspaces']]

    def getLayersQml(self, styleName):
        layersQml = []
        layers = self.getLayers()
        for layer in layers:
            layersQml.append({
                'camada': layer["nome"],
                'qml': self.getLayerStyle(layer["nome"], layer["schema"], styleName)
            })
        return layersQml
    
    def getLayerExpressionField(self):
        return [
            {
                'camadaNome': item['nome'],
                'atributos': [
                    {
                        'nome': 'descricao_erro',
                        'valor': self.getExpressionField(item['nome'])
                    }
                ]
            }
            for item in self.getLayers()
        ]

    def getLayerConditionalStyle(self):
        return [
            {
                'camadaNome': item['nome'],
                'estilos': self.getConditionalStyles(item['nome'])
            }
            for item in self.getLayers()
        ]

    def getRules(self):
        return self.getData()['rules'][:]
    
    def getLayerStyle(self, layerName, layerSchema, styleName):
        for item in self.getStyles():
            if not(
                item['f_table_schema'] == layerSchema
                and
                item['f_table_name'] == layerName
                and
                item['stylename'] == styleName
            ):
                continue
            return item['styleqml']

    def getStyles(self):
        return self.getData()['styles'][:]

    def getStyleNames(self):
        return list(set([
            item['stylename']
            for item in self.getStyles()
        ]))

    def getDatabasePassword(self):
        return self.getData()['database']['password']

    def getDatabaseUserName(self):
        return self.getData()['database']['user']

    def getDatabaseServer(self):
        return self.getData()['database']['host']

    def getDatabasePort(self):
        return self.getData()['database']['port']

    def getDatabaseName(self):
        return self.getData()['database']['name']
    
    def getQgisModels(self):
        return [
            {
                'ordem' : idx,
                'description' : item['descricao'],
                'routineType' : 'qgisModel',
                'model_xml' : item['model_xml']
            }
            for idx, item in enumerate(self.getData()['qgisModels'])
        ]

    def getRuleRoutines(self):
        format_rules_data = {}
        for i, d in enumerate(self.getRules()):
            d['tipo_estilo'] = d['grupo_regra']
            r, g, b = d['cor_rgb'].split(',')
            d['corRgb'] = [ int(r), int(g), int(b) ]
            format_rules_data[i] = d
        if not format_rules_data:
            return []
        return[ {
            'ruleStatistics' : format_rules_data, 
            'description' : "Estatísticas de regras.",
            'routineType' : 'rules'
        }]

    def getLayersFilter(self, workspaceNames):
        layers = self.getLayers()
        workspacesFilter = self.getWorkspacesFilter(workspaceNames)
        for layer in layers:
            layer.update({
                'filter': self.getLayerFilter(layer["schema"], layer["nome"], workspacesFilter)
            }) 
        return layers

    def getWorkspacesFilter(self, workspaceNames):
        geometries = []
        for workspace in self.getData()['workspaces']:
            if not( workspace['nome'] in workspaceNames):
                continue
            geometries.append("ST_GEOMFROMEWKT('{0}')".format(workspace['ewkt']))
        return '''ST_Collect(ARRAY[{0}])'''.format(','.join(geometries))

    def getActivityGroupName(self):
        """ return "{}_{}".format(
            self.getDatabaseName(), 
            self.getWorkUnitName()
        )  """
        return "{}".format(
            self.getWorkUnitName()
        )

    def getWorkUnitName(self):
        return self.getData()['dados']['atividade']['unidade_trabalho']

    def getLayerFilter(self, layerSchema, layerName, workspacesFilter):
        #if layerName == u"aux_moldura_a":
        #    return u""""mi" = '{}'""".format(self.getWorkUnitName())
        return """ST_INTERSECTS(geom, {0}) AND {1} in (SELECT {1} FROM ONLY "{2}"."{3}")""".format(
                workspacesFilter,
                'id',
                layerSchema,
                layerName,
            )

    def getFrameQuery(self):
        return "?query=SELECT geom_from_wkt('{0}') as geometry&geometry=geometry:3:{1}".format(
            self.getWorkUnitGeometry().split(';')[1],
            self.getEPSG()
        )

    def getEPSG(self):
        return self.getWorkUnitGeometry().split(';')[0].split('=')[1]

    def getFrameQml(self):
        return '''<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
            <qgis styleCategories="Symbology" version="3.4.12-Madeira">
            <renderer-v2 forceraster="0" enableorderby="0" symbollevels="0" type="singleSymbol">
                <symbols>
                <symbol name="0" alpha="1" clip_to_extent="1" type="fill" force_rhr="0">
                    <layer pass="0" locked="0" class="SimpleFill" enabled="1">
                    <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
                    <prop v="214,32,26,0" k="color"/>
                    <prop v="bevel" k="joinstyle"/>
                    <prop v="0,0" k="offset"/>
                    <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
                    <prop v="MM" k="offset_unit"/>
                    <prop v="157,0,254,255" k="outline_color"/>
                    <prop v="solid" k="outline_style"/>
                    <prop v="0.6" k="outline_width"/>
                    <prop v="MM" k="outline_width_unit"/>
                    <prop v="solid" k="style"/>
                    <data_defined_properties>
                        <Option type="Map">
                        <Option name="name" type="QString" value=""/>
                        <Option name="properties"/>
                        <Option name="type" type="QString" value="collection"/>
                        </Option>
                    </data_defined_properties>
                    </layer>
                </symbol>
                </symbols>
                <rotation/>
                <sizescale/>
            </renderer-v2>
            <blendMode>0</blendMode>
            <featureBlendMode>0</featureBlendMode>
            <layerGeometryType>2</layerGeometryType>
        </qgis>'''

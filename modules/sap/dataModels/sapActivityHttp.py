import json

class SapActivityHttp:

    def __init__(self):
        self.data = {}

    def setData(self, data):
        self.data = data

    def getData(self):
        return self.data

    def getScale(self):
        return self.getData()['dados']['atividade']['denominador_escala']

    def getNotes(self):
        notes = []
        activityData = self.getData()['dados']['atividade']
        for key in activityData:
            if 'observacao' in key and activityData[key]:
                notes.append(activityData[key])
        return notes

    def getRequirements(self):
        activityData = self.getData()['dados']['atividade']
        if 'requisitos' in activityData and activityData['requisitos']:
            return activityData['requisitos']
        return []

    def getDescription(self):
        if not self.getData():
            return ''
        return self.getData()['dados']['atividade']['nome']

    def getUserName(self):
        return self.getData()['dados']['login']

    def getId(self):
        return self.getData()['dados']['atividade']['id']

    def getTypeProductionData(self):
        return self.getData()['dados']['atividade']['dado_producao']['tipo_dado_producao_id']

    def getStepTypeId(self):
        return self.getData()['dados']['atividade']['tipo_etapa_id']

    def getMenus(self):
        formatedMenus = []
        for data in self.getData()['dados']['atividade']['menus']:
            formatedMenu = json.loads( data['definicao_menu'] )
            formatedMenu['menuName'] = data['nome']
            formatedMenus.append( formatedMenu )
        return formatedMenus

    def getActivityGroupName(self):
        """ return "{}_{}".format(
            self.getDatabaseName(), 
            self.getWorkUnitName()
        )  """
        return "{}".format(
            self.getWorkUnitName()
        )

    def getGeomGroup(self, geometryType):
        if geometryType == 0:
            return u"PONTO"
        elif geometryType == 1:
            return u"LINHA"
        elif geometryType == 2:
            return u"AREA"

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
                rules[data['ordem']]['tipo'] = 'atributo'
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
        return [ data['nome'] for data in self.getRules() ]
            
    def getLayers(self):
        layers = self.getData()['dados']['atividade']['camadas'][:]
        for layer in layers:
            layer.update({
                'filter': self.getLayerFilter(layer)
            }) 
        return layers

    def getNoteLayers(self):
        layers = self.getData()['dados']['atividade']['camadas'][:]            
        return [
            layer
            for layer in layers
            if 'camada_apontamento' in layer and layer['camada_apontamento']
        ]

    def getLayersQml(self, styleName):
        layersQml = []
        layers = self.getLayers()[:]
        for layer in layers:
            layersQml.append({
                'camada': layer["nome"],
                'qml': self.getLayerStyle(layer["nome"], layer["schema"], styleName)
            })
        return layersQml

    def getLayerStyles(self):
        layersQml = []
        layers = self.getLayers()[:]
        for layer in layers:
            layersQml.append({
                'layerName': layer["nome"],
                'styles': self.getLayerStyleList(layer["nome"], layer["schema"])
            })
        return layersQml

    def getLayerStyleList(self, layerName, layerSchema):
        styles = []
        for item in self.getData()['dados']['atividade']['estilos']:
            if not(
                item['f_table_schema'] == layerSchema
                and
                item['f_table_name'] == layerName
            ):
                continue
            styles.append({ 'name': item['stylename'], 'qml': item['styleqml'] })
        return styles

    def getLayerALiases(self):
        return [
            {
                'camadaNome': item['nome'],
                'camadaApelido': item['alias'] if 'alias' in item else '',
                'atributosApelido': item['atributos'] if 'atributos' in item else []
            }
            for item in self.getData()['dados']['atividade']['camadas']
        ]

    def getLayerActions(self):
        return [
            {
                'camadaNome': item['nome'],
                'descricao': "Doc MGCP",
                'tipo': 'OpenUrl',
                'documentacao': item['documentacao'] if 'documentacao' in item else ''
            }
            for item in self.getData()['dados']['atividade']['camadas']
        ]
    
    def getLayerDefaultFieldValue(self):
        return [
            {
                'camadaNome': item['nome'],
                'atributos': [
                    {
                        'nome': 'ultimo_usuario',
                        'valor': self.getUserId()
                    }
                ]
            }
            for item in self.getData()['dados']['atividade']['camadas']
        ]

    def getSubphaseId(self):
        return self.getData()['dados']['atividade']['subfase_id']
    
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
            for item in self.getData()['dados']['atividade']['camadas']
        ]

    def getLayerConditionalStyle(self):
        return [
            {
                'camadaNome': item['nome'],
                'estilos': self.getConditionalStyles(item['nome'])
            }
            for item in self.getData()['dados']['atividade']['camadas']
        ]

    def getRules(self):
        return self.getData()['dados']['atividade']['regras']
    
    def getLayerStyle(self, layerName, layerSchema, styleName):
        for item in self.getData()['dados']['atividade']['estilos']:
            if not(
                item['f_table_schema'] == layerSchema
                and
                item['f_table_name'] == layerName
                and
                item['stylename'] == styleName
            ):
                continue
            return item['styleqml']

    def getStylesName(self):
        return list(set([
            item['stylename']
            for item in self.getData()['dados']['atividade']['estilos']
        ]))

    def getInputs(self):
        inputs = self.getData()['dados']['atividade']['insumos'][:]
        for data in inputs:
            if not(data['tipo_insumo_id'] == 3):
                continue
            data.update({
                'usuario': self.getDatabaseUserName(),
                'senha': self.getDatabasePassword(),
                'workUnitGeometry': self.getWorkUnitGeometry()
            })
        return inputs

    def getDatabasePassword(self):
        """ if 'login_info' in self.getData()['dados']:
            return self.getData()['dados']['login_info']['senha']
        return self.getData()['senha'] """
        if self.getTypeProductionData() == 2:
            return self.getData()['dados']['login_info']['senha']
        elif self.getTypeProductionData() == 3:
            return self.getData()['senha']

    def getDatabaseUserName(self):
        """ if 'login_info' in self.getData()['dados']:
            return self.getData()['dados']['login_info']['login']
        return self.getData()['login'] """
        if self.getTypeProductionData() == 2:
            return self.getData()['dados']['login_info']['login']
        elif self.getTypeProductionData() == 3:
            return self.getData()['login']

    def getDatabaseServer(self):
        path = self.getData()['dados']['atividade']['dado_producao']['configuracao_producao']
        return path.split(':')[0]

    def getDatabasePort(self):
        path = self.getData()['dados']['atividade']['dado_producao']['configuracao_producao']
        return path.split(':')[1].split('/')[0]

    def getDatabaseName(self):
        path = self.getData()['dados']['atividade']['dado_producao']['configuracao_producao']
        return path.split(':')[1].split('/')[1]
    
    def getWorkUnitGeometry(self):
        return self.getData()['dados']['atividade']['geom']

    def getWorkUnitName(self):
        return self.getData()['dados']['atividade']['unidade_trabalho']

    def getFmeConfig(self):
        return self.getData()['dados']['atividade']['fme']
    
    def getQgisModels(self):
        return [
            {
                'ordem' : item['ordem'],
                'description' : item['descricao'],
                'routineType' : 'qgisModel',
                'model_xml' : item['model_xml']
            }
            for item in self.getData()['dados']['atividade']['models_qgis'] 
        ]

    def getRuleRoutines(self):
        rules = self.getRules()
        if not rules:
            return []
        return[ {
            'ruleStatistics' : rules[0]['regra'], 
            'description' : "Estatísticas de regras.",
            'routineType' : 'rules'
        }]
        
    def getLineage(self):
        if not( 
                'linhagem' in self.getData()['dados']['atividade'] 
                and 
                self.getData()['dados']['atividade']['linhagem'] 
            ):
            return []
        return [
            {
                'etapa': d['etapa'] if 'etapa' in d else '',
                'data_inicio': d['data_inicio'] if 'data_inicio' in d else '',
                'data_fim': d['data_fim'] if 'data_fim' in d else '',
                'posto_grad': d['posto_grad'] if 'posto_grad' in d else '',
                'nome_guerra': d['nome_guerra'] if 'nome_guerra' in d else '',
                'situacao': d['situacao'] if 'situacao' in d else '',
            }
            for d in self.getData()['dados']['atividade']['linhagem']
        ]

    def getUserId(self):
        return self.getData()['dados']['usuario_id']

    def getLayerFilter(self, layer):
        layerSchema = layer["schema"]
        layerName = layer["nome"]
        
        #if layerName == u"aux_moldura_a":
        #    return u""""mi" = '{}'""".format(self.getWorkUnitName())
        filterDefault = """ST_INTERSECTS(geom, ST_GEOMFROMEWKT('{0}')) AND {1} in (SELECT {1} FROM ONLY "{2}"."{3}")""".format(
                self.getWorkUnitGeometry(),
                'id',
                layerSchema,
                layerName,
            )
        
        if 'camada_apontamento' in layer and layer['camada_apontamento']:
            subphaseId = self.getSubphaseId()
            attributeName =  layer["atributo_filtro_subfase"]
            filterDefault += """ AND ( "{0}" = '{1}' )""".format(attributeName, subphaseId)
        return filterDefault

    def getFrameQuery(self):
        return "?query=SELECT geom_from_wkt('{0}') as geometry".format(
            self.getFrameWkt()
        )

    def getFrameWkt(self):
        return self.getWorkUnitGeometry().split(';')[1]

    def getEPSG(self):
        return self.getWorkUnitGeometry().split(';')[0].split('=')[1]

    def getProject(self):
        return self.getData()['dados']['atividade']['projeto'] if 'projeto' in self.getData()['dados']['atividade'] else '-'

    def getBlock(self):
        return self.getData()['dados']['atividade']['bloco'] if 'bloco' in self.getData()['dados']['atividade'] else '-'

    def getLot(self):
        return self.getData()['dados']['atividade']['lote'] if 'lote' in self.getData()['dados']['atividade'] else '-'

    def getScale(self):
        return '1:{}'.format(self.getData()['dados']['atividade']['denominador_escala']) if 'denominador_escala' in self.getData()['dados']['atividade'] else '-'

    def getShortcuts(self):
        return self.getData()['dados']['atividade']['atalhos']

    def getShortcutsDescription(self):
        descriptionHtml = ''
        for shortcut in self.getData()['dados']['atividade']['atalhos']:
            if shortcut['idioma'] != 'português':
                continue
            if not shortcut['atalho']:
                continue
            descriptionHtml += '<b>{0}:</b> {1}<br>'.format(
                shortcut['ferramenta'], 
                shortcut['atalho']
            )
        return '<div>{0}</div>'.format(descriptionHtml)
        return self.getData()['dados']['atividade']['atalhos']

    def getFrameQml(self):
        return '''<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
            <qgis styleCategories="Symbology" version="3.18.1-Zürich">
            <renderer-v2 type="invertedPolygonRenderer" forceraster="0" enableorderby="0" preprocessing="0">
                <renderer-v2 type="singleSymbol" forceraster="0" enableorderby="0" symbollevels="0">
                <symbols>
                    <symbol type="fill" force_rhr="0" name="0" alpha="1" clip_to_extent="1">
                    <data_defined_properties>
                        <Option type="Map">
                        <Option type="QString" name="name" value=""/>
                        <Option name="properties"/>
                        <Option type="QString" name="type" value="collection"/>
                        </Option>
                    </data_defined_properties>
                    <layer class="SimpleFill" locked="0" enabled="1" pass="0">
                        <Option type="Map">
                        <Option type="QString" name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0"/>
                        <Option type="QString" name="color" value="255,13,29,77"/>
                        <Option type="QString" name="joinstyle" value="bevel"/>
                        <Option type="QString" name="offset" value="0,0"/>
                        <Option type="QString" name="offset_map_unit_scale" value="3x:0,0,0,0,0,0"/>
                        <Option type="QString" name="offset_unit" value="MM"/>
                        <Option type="QString" name="outline_color" value="157,0,254,255"/>
                        <Option type="QString" name="outline_style" value="solid"/>
                        <Option type="QString" name="outline_width" value="0.6"/>
                        <Option type="QString" name="outline_width_unit" value="MM"/>
                        <Option type="QString" name="style" value="solid"/>
                        </Option>
                        <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
                        <prop v="255,13,29,77" k="color"/>
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
                            <Option type="QString" name="name" value=""/>
                            <Option name="properties"/>
                            <Option type="QString" name="type" value="collection"/>
                        </Option>
                        </data_defined_properties>
                    </layer>
                    </symbol>
                </symbols>
                <rotation/>
                <sizescale/>
                </renderer-v2>
            </renderer-v2>
            <blendMode>0</blendMode>
            <featureBlendMode>0</featureBlendMode>
            <layerGeometryType>2</layerGeometryType>
            </qgis>'''

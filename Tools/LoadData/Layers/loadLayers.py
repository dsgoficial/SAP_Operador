# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
import sys, os, copy, json, platform
from qgis import core, gui
from qgis.PyQt.QtXml import QDomDocument

from Ferramentas_Producao.SAP.managerSAP import ManagerSAP
from Ferramentas_Producao.Database.postgresql import Postgresql
from Ferramentas_Producao.utils.managerQgis import ManagerQgis

from Ferramentas_Producao.Tools.LoadData.Layers.generatorCustomForm import GeneratorCustomForm
from Ferramentas_Producao.Tools.LoadData.Layers.generatorCustomInitCode import GeneratorCustomInitCode
from Ferramentas_Producao.Tools.LoadData.Rules.rules import Rules
from Ferramentas_Producao.Tools.LoadData.Rules.rulesSap import RulesSap

class LoadLayers:
    def __init__(self, sap_mode, postgresql, iface, frame):
        self.iface = iface
        self.sap_mode = sap_mode
        self.rules = None
        self.postgresql = postgresql
        self.frame = frame
        self.layers_config = {
            'names' : {},
            'attr' : {},
            'doc' : {}
        }
        self.db_group = None

    def load(self, settings_data, is_menu=False):
        ManagerQgis(self.iface).save_project_var(
            'settings_user', 
            json.dumps(settings_data)
        )
        self.create_rules(settings_data)
        db_group = self.create_db_group(settings_data)
        settings_data['db_group'] = db_group
        layers_data = self.get_layers_data(settings_data[u'layers_name'])
        layers_vector = []
        for lyr_data in layers_data:
            layer_config = self.get_layer_config(lyr_data['layer_name'])
            v_lyr = self.load_layer(settings_data, lyr_data, layer_config, is_menu)
            layers_vector.append(v_lyr)
            self.frame.update_progressbar() if self.frame else ''
        if not(is_menu):
            self.create_virtual_frame(db_group)
        self.clean_empty_groups(db_group)
        self.rules = {}
        return layers_vector

    def create_rules(self, settings_data):
        rules = settings_data['rules_name']
        if rules:
            if self.sap_mode:
                self.rules = RulesSap(self.iface)
                sap_data = ManagerSAP(self.iface).load_data()
                rules_data = sap_data['dados']['atividade']['regras']
            else:
                self.rules = Rules(self.iface)
                rules_data = self.postgresql.get_rules_data()
            self.rules.rules_selected = rules
            self.rules.createRules(
                rules_data
            )

    def create_db_group(self, settings_data):
        workspace_name = self.get_workspace_name(settings_data) 
        db_group_name = u"{}_{}".format(
            self.postgresql.get_current_db_name(), 
            workspace_name
        )
        db_group = self.add_group_layer(db_group_name)
        self.db_group = db_group
        return db_group

    def get_workspace_name(self, settings_data):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            workspace_name = sap_data['unidade_trabalho']
        else:
            workspace_name = '_'.join( settings_data['workspaces'] )
        return workspace_name

    def add_group_layer(self, group_name, group=None):
        if group:
            result = group.findGroup(group_name)
        else:
            group = core.QgsProject.instance().layerTreeRoot()
            result = group.findGroup(group_name)
        if result:
            return result
        else:
            return group.addGroup(group_name)

    def get_layers_data(self, layers_name):
        def sort_group_geom(d):
            if d['group_geom'] == 'PONTO':
                return 0
            elif d['group_geom'] == 'LINHA':
                return 1
            else:
                return 2
        def sort_group_class(d):
            return d['group_class']
        layers_data = []
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()
            for data  in sap_data['dados']['atividade']['camadas']:
                name = data['nome']
                if  name in self.layers_config['names']:
                    name = self.layers_config['names'][name]
                layers_data.append( self.postgresql.get_layer_data( 
                    { 
                        'nome' : name,
                        'schema' : data['schema'] 
                    } 
                ) )
                layers_data = sorted(layers_data, key=sort_group_class)
                layers_data = sorted(layers_data, key=sort_group_geom)
        else:
            for name  in layers_name:
                if name in self.layers_config['names']:
                    name = self.layers_config['names'][name]
                layers_data.append( self.postgresql.get_layer_data( {'nome' : name} ) )
                layers_data = sorted(layers_data, key=sort_group_geom)
        return layers_data


    def get_layer_config(self, layer_name):
        layer_config = {}
        name = layer_name
        values_config = list(self.layers_config['names'].values())
        if layer_name in values_config:
            keys_config = list(self.layers_config['names'].keys())
            name = keys_config[values_config.index(layer_name)]
            layer_config = {
                'name_alias' : name, 
                'attr_alias' : {},
                'doc' : {}
            }
            if name in self.layers_config['attr']:
                layer_config['attr_alias'] = self.layers_config['attr'][name]
            if name in self.layers_config['doc']:
                layer_config['doc'] = self.layers_config['doc'][name]
        return layer_config


    def load_layer(self, settings_data, layer_data, layer_config, is_menu):
        filter_text, wkt_total = self.get_workspace_filter(settings_data, layer_data['layer_name'])
        v_lyr, loaded = self.add_layer_on_canvas(
            settings_data, 
            layer_data, 
            filter_text
        )
        if (is_menu and not(loaded)) or not(is_menu):    
            self.add_layer_style(v_lyr, settings_data)
            self.add_layer_values_map(v_lyr, layer_data)
            self.add_layer_fields_custom(v_lyr)
            self.add_layer_aliases(v_lyr, layer_config)
            self.add_custom_action_layer(v_lyr, layer_config)
            form_dump = self.add_layer_custom_form(
                v_lyr, 
                layer_data, 
                self.postgresql.get_current_db_name()
            )
            self.add_layer_variable(
                v_lyr,
                {
                    "uiData" : form_dump,
                    "area_trabalho_nome" : self.get_workspace_name(settings_data), 
                    "area_trabalho_poligono" : wkt_total
                }
            )
            if self.rules:
                self.rules.loadRulesOnlayer({
                    u"vectorLayer" : v_lyr
                })
                self.rules.add_table_rules(v_lyr)
        self.add_layer_default_values(v_lyr)
        return v_lyr

    def get_workspace_filter(self, settings_data, layer_name):
        wkt_total = ''
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            wkt_total = sap_data['geom']
            if layer_name == u"aux_moldura_a":
                filter_text = u""""mi" = '{}'""".format(workspace_name)
            else:
                filter_text = u"""ST_INTERSECTS(geom, ST_GEOMFROMEWKT('{}'))""".format(wkt_total)
        else:
            workspaces = settings_data['workspaces']
            if layer_name == u"aux_moldura_a":
                filter_text = u''' "mi" in ( {0} ) '''.format( ', '.join([ "'{0}'".format(w) for w in workspaces]) )
            else:
                frames_wkt = self.postgresql.get_frames_wkt()
                wkts = [frames_wkt[w] for w in workspaces]
                wkt_total = self.combine_wkts(wkts)
                filter_text =  u"""ST_INTERSECTS(geom, ST_GEOMFROMEWKT('{}'))""".format(wkt_total)
        return filter_text, wkt_total

    def combine_wkts(self, wkts):
        geoms = core.QgsGeometry.fromWkt('GEOMETRYCOLLECTION()')
        for wkt in wkts:
            geoms = geoms.combine(core.QgsGeometry.fromWkt(wkt.split(';')[-1]))
        epsg = wkt.split(';')[0]
        return "{0};{1}".format(epsg, geoms.asWkt())

    def add_layer_on_canvas(self, settings_data, layer_data, filter_text):
        layer_name = layer_data['layer_name']
        result = self.search_layer(layer_name, settings_data)
        if result:
            v_lyr = result
            v_lyr.setSubsetString(filter_text)
        else:
            class_group = self.get_class_group(layer_data, settings_data)
            connection_config = self.postgresql.get_connection_config()
            uri_text = self.get_uri_text(connection_config, layer_data, filter_text)
            v_lyr = core.QgsVectorLayer(uri_text, layer_name, u"postgres")
            if (
                (v_lyr and settings_data['with_geom'] and v_lyr.allFeatureIds())
                or 
                (v_lyr and not(settings_data['with_geom']))
                ):
                vl = core.QgsProject.instance().addMapLayer(v_lyr, False)
                class_group.addLayer(vl)
        return v_lyr, bool(result)


    def search_layer(self, layer_name, settings_data):
        db_name = self.postgresql.get_connection_config()['db_name']
        for layer in [ t.layer() for t in settings_data['db_group'].findLayers()]:
            data_source = layer.dataProvider().uri()
            test = (
                (db_name == data_source.database()) 
                and
                (layer_name == data_source.table())            
            )
            if test:
                return layer
        return False

    def get_class_group(self, layer_data, settings_data):
        db_group = settings_data['db_group']
        geom_group = self.add_group_layer(layer_data['group_geom'], db_group)
        class_group = self.add_group_layer(layer_data['group_class'], geom_group)
        return class_group

    def get_uri_text(self, conn_data, layer_data, filter_text):
        template_uri = u"""dbname='{}' host={} port={} user='{}' password='{}' table="{}"."{}" (geom) sql={}"""
        uri_text = template_uri.format(
            conn_data['db_name'], 
            conn_data['db_host'], 
            conn_data['db_port'], 
            conn_data['db_user'],
            conn_data['db_password'],
            layer_data['layer_schema'],
            layer_data['layer_name'],
            filter_text
        )
        return uri_text

    def add_layer_style(self, v_lyr, settings_data):
        data_source = v_lyr.dataProvider().uri()
        layer_name = data_source.table()
        style_selected = settings_data[u"style_name"]
        style_xml = ''
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()
            for style_data in sap_data['dados']['atividade']['estilos']:
                if ( 
                    style_data['stylename'] == style_selected
                    and 
                    style_data['f_table_name'] == layer_name
                    ):
                    style_xml = style_data['styleqml']
                    break
        else:
            #mudar
            v_lyr.loadDefaultStyle()
            if style_selected:
                styles_data = self.postgresql.get_styles_data()
                for style_name in styles_data:
                    if (style_selected in style_name) and (layer_name in style_name):
                        style_id = str(styles_data[style_name])
                        style_xml = v_lyr.getStyleFromDatabase(style_id)[0]
                        break
        doc = QDomDocument()
        doc.setContent(style_xml)
        v_lyr.importNamedStyle(doc)

    def add_layer_values_map(self, v_lyr, layer_data):
        fields_map = self.get_layer_fields_map(v_lyr) 
        for name in fields_map:
            field_index = fields_map[name]
            v_lyr.setFieldAlias(field_index, name)
            is_value_map = (
                (name in layer_data['layer_fields']) 
                and 
                (
                    u"valuemap" in [
                        n.lower() for n in list(layer_data['layer_fields'][name].keys())
                    ]
                )
            )
            if is_value_map:
                values = copy.deepcopy(layer_data['layer_fields'][name][u"valueMap"])
                if values and u"IGNORAR" in values:
                    del values[u"IGNORAR"]
                setup = core.QgsEditorWidgetSetup( 
                    'ValueMap', 
                    { 'map': values }
                )                
                v_lyr.setEditorWidgetSetup(field_index, setup)

    def add_layer_fields_custom(self, v_lyr):
        if v_lyr.geometryType() == 1:
            v_lyr.addExpressionField(
                u"$length",
                core.QgsField(u"length_otf", QtCore.QVariant.Double)
            )
        elif v_lyr.geometryType() == 2:
            v_lyr.addExpressionField(
                u"$area",
                core.QgsField(u"area_otf", QtCore.QVariant.Double)
            )

    def add_layer_aliases(self, v_lyr, layer_config):
        if layer_config:
            self.add_layer_variable(v_lyr, {'layer_name' : v_lyr.name()})
            v_lyr.setName(layer_config['name_alias'])
            for field_conf in layer_config['attr_alias']:
                field_idx = v_lyr.fields().indexOf(field_conf["nome"])
                if field_idx > 0:
                    v_lyr.setFieldAlias(field_idx, field_conf["alias"])

    def add_layer_custom_form(self, v_lyr, layer_data, db_name):
        fields_sorted = self.get_sorted_layer_fields(v_lyr, layer_data) 
        form_name = u"{}_{}.ui".format(db_name, layer_data['layer_name'])
        form_file = self.get_form_file(form_name)
        gen_form = GeneratorCustomForm()
        gen_form.create(
            form_file, 
            layer_data, 
            fields_sorted,
            v_lyr
        )
        form_config = self.get_form_config_qgis(
            v_lyr, 
            form_file.name, 
            layer_data
        )
        v_lyr.setEditFormConfig(form_config)
        data_dump = json.dumps({
            u"uiData" : {
                    u"layer_data" : layer_data,
                    u"fields_sorted" : fields_sorted,
                    u"form_name" : form_file.name
                }
            }, 
            ensure_ascii=False
        )
        return data_dump 

    def add_layer_default_values(self, v_lyr):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']
            idx = v_lyr.fields().indexOf('ultimo_usuario')
            confField = v_lyr.defaultValueDefinition(idx)
            confField.setExpression("'{0}'".format(sap_data['usuario_id']))
            v_lyr.setDefaultValueDefinition(idx, confField)
    

    def add_layer_variable(self, v_lyr, data_dump):
        for name in data_dump:
            core.QgsExpressionContextUtils.setLayerVariable(
                v_lyr,
                name,
                data_dump[name]
            )

    def add_custom_action_layer(self, v_lyr, layer_config):
        if self.sap_mode and 'doc' in layer_config and layer_config['doc']:
            custom_action = core.QgsAction(
                core.QgsAction.OpenUrl, 
                "Doc MGCP", 
                "[%'{}'%]".format(
                    layer_config['doc']
                )
            )
            custom_action.setActionScopes({'Feature', 'Canvas'})
            v_lyr.actions().addAction(custom_action)

    def get_form_file(self, form_name):
        form_path = os.path.join(
            os.path.dirname(__file__),
            u"forms",
            form_name
        ) 
        return open(form_path, "w")

    def reload_forms_custom(self):
        m_qgis = ManagerQgis(self.iface)
        for v_lyr in m_qgis.get_loaded_layers():
            data = core.QgsExpressionContextUtils.layerScope(v_lyr).variable(u"uiData")
            if v_lyr.type() == core.QgsMapLayer.VectorLayer and data:
                json_data = json.loads(data)
                if 'uiData' in json_data:
                    ui_data = json.loads(data)['uiData']
                    form_file = self.get_form_file(ui_data['form_name'])
                    form_custom = GeneratorCustomForm()
                    form_custom.create(
                        form_file,
                        ui_data["layer_data"],
                        ui_data["fields_sorted"],
                        v_lyr
                    )

    def clean_empty_groups(self, g1):
        for g2 in g1.children():
            if g2.name() != u"MOLDURA_E_INSUMOS":
                for g3 in g2.children():
                    if len(g3.children()) == 0 and g3.name() != u"MOLDURA_E_INSUMOS":
                        g2.removeChildNode(g3)

    def create_custom_code_init(self, layer_data):
        rules_form = []
        if self.rules:
            rules_form = self.rules.get_rules_form(layer_data["layer_name"])  
        gen_code = GeneratorCustomInitCode()
        if 'filter' in layer_data["layer_fields"]:
            filter_data = layer_data["layer_fields"]["filter"]
            code_init =  gen_code.getInitCodeWithFilter(filter_data, rules_form)
        else:
            code_init =  gen_code.getInitCodeWithoutFilter(rules_form)
        return code_init
    
    def get_form_config_qgis(self, v_lyr, file_name, layer_data):
        editFormConfig = v_lyr.editFormConfig()
        editFormConfig.setInitCodeSource(2)
        editFormConfig.setLayout(2)
        editFormConfig.setUiForm(file_name)
        editFormConfig.setInitFunction("formOpen")
        code_init = self.create_custom_code_init(layer_data)
        editFormConfig.setInitCode(code_init)
        return editFormConfig
    
    def create_virtual_frame(self, db_group):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            srid = sap_data['geom'].split(';')[0].split('=')[1]
            wkt = sap_data['geom'].split(';')[1]
            query = "?query=SELECT geom_from_wkt('{0}') as geometry&geometry=geometry:3:{1}".format(
                wkt,
                srid
            )
            lyr_virtual = core.QgsVectorLayer(query, "moldura", "virtual")
            vl = core.QgsProject.instance().addMapLayer(lyr_virtual, False)
            style_path = os.path.join(
                os.path.dirname(__file__),
                "styles",
                "frame_sap.qml"
            ) 
            vl.loadNamedStyle(style_path)
            frame_group = self.add_group_layer("MOLDURA_E_INSUMOS", db_group)
            if not(vl.name() in [l.name() for l in frame_group.findLayers()]):
                frame_group.addLayer(vl)
                 
    def get_layer_fields_map(self, v_lyr):
        conf = v_lyr.fields()
        fields_index = conf.allAttributesList()
        fields_map = { conf.field(i).name() : i for i in fields_index}
        return fields_map

    def get_sorted_layer_fields(self, v_lyr, layer_data):
        fields_sorted = []
        if u"nome" in layer_data['layer_fields']:
            fields_sorted.append(u"nome")
        if u"filter" in layer_data['layer_fields']:
            fields_sorted.append(u"filter")
            fields_sorted.append(u"tipo")
        for field in layer_data['layer_fields']:
            if not(field in fields_sorted):
                fields_sorted.append(field)
        return fields_sorted
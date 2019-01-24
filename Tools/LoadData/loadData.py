# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from .loadDataFrame import LoadDataFrame
from .generatorCustomForm import GeneratorCustomForm
from .generatorCustomInitCode import GeneratorCustomInitCode
import sys, os, copy, json, platform
from qgis import core, gui
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from SAP.managerSAP import ManagerSAP
from Database.postgresql import Postgresql
from Tools.Rules.rules import Rules
from utils import managerFile

class LoadData(QtCore.QObject):

    show_menu = QtCore.pyqtSignal()

    def __init__(self, iface):
        super(LoadData, self).__init__()
        self.iface = iface
        self.sap_mode = False
        self.postgresql = Postgresql()
        self.postgresql.set_connections_data()
        self.rules = None
        self.frame = None
    
    def load_data(self, settings_data):
        db_data = self.postgresql.load_data()
        db_data['settings_user'] = settings_data
        self.load_layers(settings_data, db_data) if settings_data['layers_name'] else ''
        self.load_input_files(settings_data) if settings_data['input_files'] else ''
        self.postgresql.dump_data(db_data)
        self.show_menu.emit() if settings_data['with_menu'] else ''
        self.frame.show()
    
    def get_frame(self):
        self.frame = LoadDataFrame(self.iface)
        if self.sap_mode:
            self.config_sap_mode()
            self.frame.config_sap_mode()
        else:
            dbs = [u"<Opções>"] + sorted(self.postgresql.get_dbs_name())
            self.frame.load_dbs_name(dbs)
            self.frame.database_load.connect(
                self.update_frame
            )
        self.frame.load_data.connect(
            self.load_data
        )
        return self.frame

    def validate_layers_sap(self, layers_sap, db_json):
        layers_list = [ ]
        for g in db_json['db_layers']:
            for d in db_json['db_layers'][g]:
                layers_list.append(d['layer_name'])
        return [ n for n in layers_sap if n in layers_list] 
    
    def validate_rules_sap(self, rules_sap, db_json):
        rules_name = list(set([
            db_json['db_rules'][i]['tipo_estilo'] for i in db_json['db_rules'] 
        ])) if db_json['db_rules'] else []
        return [ n for n in rules_sap if n in rules_name ] 
    
    def validate_styles_sap(self, styles_sap, db_json):
        styles_name = list(set([ d.split('_')[0] for d in db_json['db_styles'].keys()]))
        return [ n for n in styles_sap if n in styles_name ]

    def config_sap_mode(self):
        sap_data = ManagerSAP().load_data()
        db_data = sap_data['dados']['atividade']['banco_dados']
        db_name = db_data['nome']
        self.postgresql.set_connections_data({
            'db_name' : db_name,
            'db_host' : db_data['servidor'],
            'db_port' : db_data['porta'],
            'db_user' : sap_data['user'],
            'db_password' : sap_data['password'] 
        })
        db_json = self.postgresql.load_db_json(db_name)
        layers_sap = [ d['nome'] for d in sap_data['dados']['atividade']['camadas']]
        validated_layers =  self.validate_layers_sap(layers_sap, db_json)
        rules_sap = sap_data['dados']['atividade']['regras']
        validated_rules = self.validate_rules_sap(rules_sap, db_json)
        styles_sap = sap_data['dados']['atividade']['estilos']
        validated_styles = self.validate_styles_sap(styles_sap, db_json)
        self.input_files = sap_data['dados']['atividade']['insumos']
        self.frame.load({
            'rules' : sorted(validated_rules),
            'layers' : sorted(validated_layers),
            'styles' : sorted(validated_styles),
            'input_files' : sorted([ d['nome'] for d in self.input_files]),
            'workspaces' : []
        })

    def update_frame(self, db_name):
        db_data = self.postgresql.load_db_json(db_name)
        layers_list = [ ]
        db_layers = db_data['db_layers']
        for g in db_layers:
            for d in db_layers[g]:
                layers_list.append(d['layer_name'])
        rules_name = []
        db_rules = db_data['db_rules']
        if db_rules:
            rules_name = sorted(list(set([
                db_rules[i]['tipo_estilo'] 
                for i in db_rules 
            ])))
        styles_name = sorted(list(set([ 
            d.split('_')[0] 
            for d in db_data['db_styles'].keys()
        ])))
        workspaces_name = sorted(db_data['db_workspaces_name'])
        self.frame.load({
            'rules' : rules_name,
            'layers' : sorted(layers_list),
            'styles' : styles_name,
            'input_files' : [],
            'workspaces' : [u"Todas"] + workspaces_name
        })

    def get_map_layers(self, layers_data):
        return { data[u'layer_name'] : idx for idx, data in enumerate(layers_data)}

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

    def get_spatial_filter(self, layer_name, workspace_name, workspace_wkt):
        if layer_name == u"aux_moldura_a":
            filter_text = u""""mi" = '{}'""".format(workspace_name)
        else:
            filter_text = u"""ST_INTERSECTS(geom, ST_GEOMFROMEWKT('{}'))""".format(workspace_wkt)
        return filter_text

    def add_layer_variable(self, v_lyr, data_dump):
        for name in data_dump:
            core.QgsExpressionContextUtils.setLayerVariable(
                v_lyr,
                name,
                data_dump[name]
            )

    def add_layer_style(self, v_lyr, settings_data, db_data):
        v_lyr.loadDefaultStyle()
        style_selected = settings_data[u"style_name"]
        if style_selected:
            layer_name = v_lyr.name()
            styles_data = db_data[u'db_styles']
            for style_name in styles_data:
                if (style_selected in style_name) and (layer_name in style_name):
                    style_id = str(styles_data[style_name])
                    style_xml = v_lyr.getStyleFromDatabase(style_id)[0]
                    v_lyr.loadNamedStyle(style_xml)
                    
    def get_layer_fields_map(self, v_lyr):
        conf = v_lyr.fields()
        fields_index = conf.allAttributesList()
        fields_map = { conf.field(i).name() : i for i in fields_index}
        return fields_map

    def add_layer_values_map(self, v_lyr, layer_data):
        fields_map = self.get_layer_fields_map(v_lyr) 
        for name in fields_map:
            is_value_map = (
                (name in layer_data['layer_fields']) and 
                (u"valueMap" in layer_data['layer_fields'][name])
            )
            if is_value_map:
                field_index = fields_map[name]
                values = copy.deepcopy(layer_data['layer_fields'][name][u"valueMap"])
                if u"IGNORAR" in values:
                    del values[u"IGNORAR"]
                setup = core.QgsEditorWidgetSetup( 'ValueMap', {
                         'map': values
                        }
                      )                
                v_lyr.setEditorWidgetSetup(field_index, setup)

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

    def get_form_file(self, form_name):
        form_path = os.path.join(
            os.path.dirname(__file__),
            u"forms",
            form_name
        ) 
        return open(form_path, "w")

    def reload_forms_custom(self):
        for v_lyr in core.QgsProject.instance().mapLayers().values():
            data = core.QgsExpressionContextUtils.layerScope(v_lyr).variable(u"uiData")
            if v_lyr.type() == core.QgsMapLayer.VectorLayer and data:
                ui_data = json.loads(data)['uiData']
                form_file = self.get_form_file(ui_data['form_name'])
                form_custom = GeneratorCustomForm()
                form_custom.create(
                    form_file,
                    ui_data["layer_data"],
                    ui_data["fields_sorted"],
                    v_lyr
                )

    def clean_forms_custom(self):
        directory_path = os.path.join(
            os.path.dirname(__file__),
            'forms'
        )
        file_name_list = [ 
            name for name in os.listdir(directory_path)
            if not('.py' in name)
        ]
        [ os.remove(os.path.join(directory_path, name)) for name in file_name_list]

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

    def collapse_all(self, g1):
        g1.setExpanded(False)
        for g2 in g1.children():
            g2.setExpanded(False)
            for g3 in g2.children():
                g3.setExpanded(False)
                for g4 in g3.children():
                    g4.setExpanded(False)

    def clean_empty_groups(self, g1):
        for g2 in g1.children():
            if g2.name() != u"MOLDURA":
                for g3 in g2.children():
                    if len(g3.children()) == 0 and g3.name() != u"MOLDURA":
                        g2.removeChildNode(g3)

    def add_layer_on_canvas(self, settings_data, db_data, layer_data, filter_text):
        layer_name = layer_data['layer_name']
        class_group = self.get_class_group(layer_data, settings_data)
        layers = class_group.findLayers()
        result = [ l.layer() for l in layers if l and l.layer().name() == layer_name]
        if result:
            v_lyr = result[0]
            v_lyr.setSubsetString(filter_text)
        else:
            conn_data = db_data[u"db_connection"]
            uri_text = self.get_uri_text(conn_data, layer_data, filter_text)
            v_lyr = core.QgsVectorLayer(uri_text, layer_name, u"postgres")
        if (
                (v_lyr and settings_data['with_geom'] and v_lyr.allFeatureIds())
                or 
                (v_lyr and not(settings_data['with_geom']))
            ):
            vl = core.QgsProject.instance().addMapLayer(v_lyr, False)
            class_group.addLayer(vl)
        return v_lyr

    def load_layer(self, settings_data, db_data, layer_data):
        if self.sap_mode:
            sap_data = ManagerSAP().load_data()['dados']['atividade']
            workspace_name = sap_data['unidade_trabalho']
            workspace_wkt = sap_data['geom']
        else:
            workspace_name = settings_data['workspace_name'] 
            workspace_wkt = '' if workspace_name == u"Todas" else (
                db_data['db_workspaces_wkt'][workspace_name]
            )
        filter_text = '' 
        if workspace_wkt != '':
            filter_text = self.get_spatial_filter(
                layer_data['layer_name'], 
                workspace_name, 
                workspace_wkt
            )
        v_lyr = self.add_layer_on_canvas(
            settings_data, 
            db_data, 
            layer_data, 
            filter_text
        )    
        self.add_layer_style(v_lyr, settings_data, db_data)
        self.add_layer_values_map(v_lyr, layer_data)
        self.add_layer_fields_custom(v_lyr)
        form_dump = self.add_layer_custom_form(
            v_lyr, 
            layer_data, 
            db_data['db_name']
        )
        self.add_layer_variable(
            v_lyr,
            {
                u"uiData" : form_dump,
                u"area_trabalho_nome" : workspace_name, 
                u"area_trabalho_poligono" : workspace_wkt
            }
        )
        if self.rules:
            self.rules.loadRulesOnlayer({
                u"vectorLayer" : v_lyr
            })
            self.rules.add_table_rules(v_lyr)
        return v_lyr

    def sort_layers_selected(self, layers_list):
        def custom_sort(a):
            if a.split('_')[-1] == 'p':
                return 0
            elif a.split('_')[-1] == 'l':
                return 1
            else:
                return 2
        return sorted(layers_list, key=custom_sort)

    def create_rules(self, settings_data, db_data):
        rules = settings_data['rules_name']
        if rules:
            self.rules = Rules(self.iface)
            self.rules.rules_selected = rules
            self.rules.createRules(db_data['db_rules'])

    def create_db_group(self, settings_data, db_data):
        if self.sap_mode:
            sap_data = ManagerSAP().load_data()['dados']['atividade']
            workspace_name = sap_data['unidade_trabalho']
        else:
            workspace_name = settings_data['workspace_name'] 
        db_group_name = u"{}_{}".format(db_data['db_name'], workspace_name)
        db_group = self.add_group_layer(db_group_name)
        return db_group
    
    def create_virtual_frame(self, db_group):
        if self.sap_mode:
            sap_data = ManagerSAP().load_data()['dados']['atividade']
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
            frame_group = self.add_group_layer("MOLDURA", db_group)
            frame_group.addLayer(vl)
            

    def load_layers(self, settings_data, db_data):
        self.create_rules(settings_data, db_data)
        db_group = self.create_db_group(settings_data, db_data)
        settings_data['db_group'] = db_group
        layers_data = db_data['db_layers']
        layers_data = layers_data[u'PONTO']+layers_data[u'LINHA']+layers_data[u'AREA']
        layers_map = self.get_map_layers(layers_data)
        layers_list = self.sort_layers_selected(settings_data[u'layers_name'])
        layers_vector = []
        for layer_name in layers_list:
            p = layers_map[layer_name]
            layer_data = layers_data[p]
            v_lyr = self.load_layer(
                settings_data, 
                db_data,
                layer_data
            )
            self.add_layer_default_values(v_lyr)
            layers_vector.append(v_lyr)
            self.frame.update_progressbar() if self.frame else ''
        self.create_virtual_frame(db_group)
        self.collapse_all(db_group)
        self.clean_empty_groups(db_group)
        self.rules = {}
        return layers_vector
        
    def load_input_files(self, settings_data):
        if self.sap_mode:
            sap_data = ManagerSAP().load_data()
            paths_data = {
                d['nome'] : d['caminho']
                for d in sap_data['dados']['atividade']['insumos'] 
                if d['nome'] in settings_data['input_files']
            }
            files_data = managerFile.download(paths_data)
            erro = []
            for n in files_data:
                file_path = files_data[n]
                r = self.add_raster_layer(n, file_path)
                if not(r):
                    erro.append(file_path)
            self.frame.show_erro(erro) if len(erro) > 0 else ''

    def add_raster_layer(self, raster_name, raster_path):
        layer = core.QgsRasterLayer(raster_path, raster_name)
        if layer.isValid():
            core.QgsProject.instance().addMapLayer(layer)
            return True
        return False
            
    def add_layer_default_values(self, v_lyr):
        if self.sap_mode:
            sap_data = ManagerSAP().load_data()['dados']
            idx = v_lyr.fields().indexOf('ultimo_usuario')
            confField = v_lyr.defaultValueDefinition(idx)
            confField.setExpression("'{0}'".format(sap_data['usuario_id']))
            v_lyr.setDefaultValueDefinition(idx, confField)



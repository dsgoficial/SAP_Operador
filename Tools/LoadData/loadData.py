# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from .loadDataFrame import LoadDataFrame
from .generatorCustomForm import GeneratorCustomForm
from .generatorCustomInitCode import GeneratorCustomInitCode
from .rules import Rules
import sys, os, copy, json, platform
from qgis import core, gui
from qgis.PyQt.QtXml import QDomDocument
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from SAP.managerSAP import ManagerSAP
from Database.postgresql import Postgresql
from utils import managerFile
from utils.managerQgis import ManagerQgis


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
        self.layers_config = {
            'names' : {},
            'attr' : {},
            'doc' : {}
        }
    
    def load_data(self, settings_data):
        self.load_layers(settings_data) if settings_data['layers_name'] else ''
        self.load_input_files(settings_data) if settings_data['input_files'] else ''
    
    def get_frame(self):
        self.frame = LoadDataFrame(self.iface)
        self.frame.menu_selected.connect(
            self.show_menu.emit
        )
        if self.sap_mode:
            self.frame.load({
                'rules' : self.get_rules_list(),
                'layers' : self.get_layers_list(),
                'styles' : self.get_styles_list(),
                'input_files' : self.get_input_files_list(),
                'workspaces' : self.get_workspaces_list()
            })
            self.frame.config_sap_mode()
        else:
            dbs_name = sorted(self.postgresql.get_dbs_names())
            dbs_name = [u"<Opções>"] + dbs_name
            self.frame.load_dbs_name(dbs_name)
            self.frame.database_load.connect(
                self.update_frame
            )
        self.frame.load_data.connect(
            self.load_data
        )
        return self.frame

    def get_layers_list(self):
        layers_names = self.postgresql.get_layers_names()
        layers_list = []
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()
            for d in sap_data['dados']['atividade']['camadas']:
                lyr_name = d['nome'] 
                if 'alias' in d:
                    name = d['alias']
                    self.layers_config['names'][name] = lyr_name
                    self.layers_config['attr'][name] = d['atributos']
                else:
                    name = lyr_name
                if 'documentacao' in d:
                    self.layers_config['doc'][name] = d['documentacao']
                layers_list.append(name) if lyr_name in layers_names else ''
        else:
            layers_list = layers_names 
        return sorted(layers_list)
    
    def get_rules_list(self):
        rules_names = self.postgresql.get_rules_names()
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()
            rules_sap = sap_data['dados']['atividade']['regras']
            rules_names = [ n for n in rules_sap if n in rules_names ] 
        return sorted(rules_names)
    
    def get_styles_list(self):
        styles_names = self.postgresql.get_styles_names()
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()
            styles_sap = sap_data['dados']['atividade']['estilos']
            styles_names = [ n for n in styles_sap if n in styles_names ] 
        return sorted(styles_names)

    def get_input_files_list(self):
        input_files_list = []
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            input_files_list = [ d['nome'] for d in sap_data['insumos'] ]
        return sorted(input_files_list)
    
    def get_workspaces_list(self):
        if self.sap_mode:
            workspaces_names = []
        else:
            workspaces_names = [u"Todas"] + self.postgresql.get_frames_names()
        return workspaces_names

    def update_frame(self, db_name=''):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()
            db_connection = sap_data['dados']['atividade']['banco_dados']
            db_name = db_connection['nome']
            self.postgresql.set_connections_data({
                'db_name' : db_name,
                'db_host' : db_connection['servidor'],
                'db_port' : db_connection['porta'],
                'db_user' : sap_data['user'],
                'db_password' : sap_data['password'] 
            })
        self.postgresql.load_db_json(db_name, sap_mode=self.sap_mode)
        
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

    def add_layer_style(self, v_lyr, settings_data):
        v_lyr.loadDefaultStyle()
        style_selected = settings_data[u"style_name"]
        if style_selected:
            data_source = v_lyr.dataProvider().uri()
            layer_name = data_source.table()
            styles_data = self.postgresql.get_styles_data()
            for style_name in styles_data:
                if (style_selected in style_name) and (layer_name in style_name):
                    style_id = str(styles_data[style_name])
                    style_xml = v_lyr.getStyleFromDatabase(style_id)[0]
                    doc = QDomDocument()
                    doc.setContent(style_xml)
                    v_lyr.importNamedStyle(doc)

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
                    
    def get_layer_fields_map(self, v_lyr):
        conf = v_lyr.fields()
        fields_index = conf.allAttributesList()
        fields_map = { conf.field(i).name() : i for i in fields_index}
        return fields_map

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

    def clean_empty_groups(self, g1):
        for g2 in g1.children():
            if g2.name() != u"MOLDURA":
                for g3 in g2.children():
                    if len(g3.children()) == 0 and g3.name() != u"MOLDURA":
                        g2.removeChildNode(g3)

    def search_layer(self, layer_name):
        db_name = self.postgresql.get_connection_config()['db_name']
        m_qgis = ManagerQgis(self.iface)
        layers = m_qgis.get_loaded_layers()
        for layer in layers:
            data_source = layer.dataProvider().uri()
            test = (
                (db_name == data_source.database()) 
                and
                (layer_name == data_source.table())            
            )
            if test:
                return layer
        return False

    def add_layer_on_canvas(self, settings_data, layer_data, filter_text):
        layer_name = layer_data['layer_name']
        result = self.search_layer(layer_name)
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

    def get_workspace_data(self, settings_data):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            workspace_name = sap_data['unidade_trabalho']
            workspace_wkt = sap_data['geom']
        else:
            workspace_name = settings_data['workspace_name'] 
            frames_wkt = self.postgresql.get_frames_wkt()
            workspace_wkt = '' if workspace_name == u"Todas" else (
                frames_wkt[workspace_name]
            )
        return workspace_name, workspace_wkt

    def create_rules(self, settings_data):
        rules = settings_data['rules_name']
        if rules:
            self.rules = Rules(self.iface)
            self.rules.rules_selected = rules
            self.rules.createRules(
                self.postgresql.get_rules_data()
            )

    def create_db_group(self, settings_data):
        workspace_name, _ = self.get_workspace_data(settings_data) 
        db_group_name = u"{}_{}".format(
            self.postgresql.get_current_db_name(), 
            workspace_name
        )
        db_group = self.add_group_layer(db_group_name)
        return db_group
    
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
            frame_group = self.add_group_layer("MOLDURA", db_group)
            if not(vl.name() in [l.name() for l in frame_group.findLayers()]):
                frame_group.addLayer(vl)

    def add_layer_aliases(self, v_lyr, layer_config):
        if layer_config:
            self.add_layer_variable(v_lyr, {'layer_name' : v_lyr.name()})
            v_lyr.setName(layer_config['name_alias'])
            for field_conf in layer_config['attr_alias']:
                field_idx = v_lyr.fields().indexOf(field_conf["nome"])
                if field_idx > 0:
                    v_lyr.setFieldAlias(field_idx, field_conf["alias"])
        

    def load_layer(self, settings_data, layer_data, layer_config, is_menu):
        workspace_name, workspace_wkt = self.get_workspace_data(settings_data)
        filter_text = '' 
        if workspace_wkt != '':
            filter_text = self.get_spatial_filter(
                layer_data['layer_name'], 
                workspace_name, 
                workspace_wkt
            )
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
        self.add_layer_default_values(v_lyr)
        return v_lyr

    def get_layers_data(self, layers_name):
        def custom_sort(d):
            if d['group_geom'] == 'PONTO':
                return 0
            elif d['group_geom'] == 'LINHA':
                return 1
            else:
                return 2
        layers_data = []
        for name  in layers_name:
            if name in self.layers_config['names']:
                name = self.layers_config['names'][name]
            layers_data.append(self.postgresql.get_layer_data(name))
        return sorted(layers_data, key=custom_sort)

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

    def load_layers(self, settings_data, is_menu=False):
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
        
    def load_input_files(self, settings_data):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()
            paths_data = [
                { 
                    'file_name' : d['nome'],
                    'path_origin' : d['caminho'],
                    'epsg' : d['epsg']
                }
                for d in sap_data['dados']['atividade']['insumos'] 
                if d['nome'] in settings_data['input_files']
            ]
            files_data = managerFile.download(paths_data)
            erro = []
            for f_data in files_data:
                path_file = f_data['path_file']
                file_name = f_data['file_name']
                epsg = f_data['epsg']
                r = self.add_raster_layer(file_name, path_file, epsg)
                if not(r):
                    erro.append(path_file)
            self.frame.show_erro(erro) if len(erro) > 0 else ''

    def add_raster_layer(self, raster_name, raster_path, epsg):
        s = QtCore.QSettings()
        val_bkp = s.value("Projections/defaultBehavior")
        s.setValue("Projections/defaultBehavior", "useGlobal")
        crs = core.QgsCoordinateReferenceSystem(int(epsg))
        layer = core.QgsRasterLayer(raster_path, raster_name)
        layer.setCrs(crs)
        s.setValue("Projections/defaultBehavior", val_bkp)
        if layer.isValid():
            core.QgsProject.instance().addMapLayer(layer)
            return True
        return False
            
    def add_layer_default_values(self, v_lyr):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']
            idx = v_lyr.fields().indexOf('ultimo_usuario')
            confField = v_lyr.defaultValueDefinition(idx)
            confField.setExpression("'{0}'".format(sap_data['usuario_id']))
            v_lyr.setDefaultValueDefinition(idx, confField)



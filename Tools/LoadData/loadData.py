# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
import sys, os, copy, json, platform
from qgis import core, gui
from qgis.PyQt.QtXml import QDomDocument

from Ferramentas_Producao.SAP.managerSAP import ManagerSAP
from Ferramentas_Producao.Database.postgresql import Postgresql
from Ferramentas_Producao.utils.managerQgis import ManagerQgis

from Ferramentas_Producao.Tools.LoadData.Inputs.loadInputs import LoadInputs
from Ferramentas_Producao.Tools.LoadData.Layers.loadLayers import LoadLayers
from Ferramentas_Producao.Tools.LoadData.Layers.generatorCustomForm import GeneratorCustomForm
from Ferramentas_Producao.Tools.LoadData.Layers.generatorCustomInitCode import GeneratorCustomInitCode

from Ferramentas_Producao.Tools.LoadData.Views.loadDataFrame import LoadDataFrame
from Ferramentas_Producao.Tools.LoadData.Views.loadDataFrame import LoadDataFrame


class LoadData(QtCore.QObject):

    show_menu = QtCore.pyqtSignal()
    restart_validate = QtCore.pyqtSignal()

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

    def clean_forms_custom(self):
        directory_path = os.path.join(
            os.path.dirname(__file__),
            'Layers',
            'forms'
        )
        file_name_list = [ 
            name for name in os.listdir(directory_path)
            if not('.py' in name)
        ]
        [ os.remove(os.path.join(directory_path, name)) for name in file_name_list]
    
    def load_data(self, settings_data):
        load_layers = LoadLayers(self.sap_mode, self.postgresql, self.iface, self.frame, self.layers_config)
        load_layers.load(settings_data) if settings_data['layers_name'] else ''
        LoadInputs(self.iface, self.postgresql, load_layers, self.frame).load(settings_data) if settings_data['input_files'] and self.sap_mode else ''
        self.restart_validate.emit()
    
    def get_frame(self):
        self.frame = LoadDataFrame(self.iface, self.sap_mode)
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
            sap_data = ManagerSAP(self.iface).load_data()
            if not sap_data['dados']['atividade']['menus']:
                self.frame.load_menu.setVisible(False)
            self.frame.config_sap_mode()
        else:
            #self.frame.tabWidget.removeTab(2)
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
                else:
                    name = lyr_name
                if 'atributos' in d:
                    self.layers_config['attr'][name] = d['atributos']
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
            rules_names = list(set([ d['grupo_regra'] for d in rules_sap ]))
        return sorted(rules_names)
    
    def get_styles_list(self):
        styles_names = self.postgresql.get_styles_names()
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()
            styles_sap = sap_data['dados']['atividade']['estilos']
            styles_names = list(set([ d['stylename'] for d in styles_sap ]))
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
            workspaces_names = self.postgresql.get_frames_names()
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
        self.postgresql.load_db_json(db_name, sap_mode=self.sap_mode) if db_name else ''
        if not self.sap_mode:
            self.frame.load({
                'rules' : self.get_rules_list(),
                'layers' : self.get_layers_list(),
                'styles' : self.get_styles_list(),
                'input_files' : self.get_input_files_list(),
                'workspaces' : self.get_workspaces_list()
            })
        
    def reload_forms_custom(self):
        LoadLayers(self.sap_mode, self.postgresql, self.iface, self.frame, self.layers_config).reload_forms_custom()

    def create_db_group(self, settings):
        load_layers = LoadLayers(self.sap_mode, self.postgresql, self.iface, self.frame, self.layers_config)
        return load_layers.create_db_group(settings)

    def search_layer(self, layer_name, settings_data):
        load_layers = LoadLayers(self.sap_mode, self.postgresql, self.iface, self.frame, self.layers_config)
        return load_layers.search_layer(layer_name, settings_data)

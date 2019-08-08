# -*- coding: utf-8 -*-
from PyQt5 import QtCore
from .menuDock import MenuDock
from .classification import Classification
from .reclassifyForm import ReclassifyForm
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from SAP.managerSAP import ManagerSAP
from Database.postgresql import Postgresql
from Tools.LoadData.loadData import LoadData
from utils import managerFile


class Menu(QtCore.QObject):

    def __init__(self, iface):
        super(Menu, self).__init__()
        self.iface = iface
        self.sap_mode = False
        self.menu_dock = None
        self.postgresql = Postgresql()
        self.postgresql.set_connections_data()
        self.classification = Classification(self.iface)
        self.classification.reclassify_form.connect(
            self.open_reclassify_form
        )
        self.path_data = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.pickle')

    def dump_data(self, data):
        managerFile.dump_data(self.path_data, data)

    def load_data(self):
        return managerFile.load_data(self.path_data)
    
    def save_profile_on_db(self, profile_name):
        profile_data = self.load_data()
        profile_data['nome_do_perfil'] = profile_name
        menu_data = {}
        menu_data['menu_name'] = profile_data['nome_do_perfil']
        menu_data['menu_profile'] = profile_data['perfil']
        menu_data['menu_order'] = profile_data['orderMenu']
        return self.postgresql.save_menu_profile(menu_data)
         

    def get_profiles_name(self):
        profiles_name = self.postgresql.get_menu_profile_names()
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']        
            profiles_name = [
                n for n in profiles_name
                if n in sap_data['menus']
            ]
        profiles_name = [u"<Vazio>"] + profiles_name
        return profiles_name

    def connect_menu_dock_signals(self):
        signals = {
            self.menu_dock.active_button : self.active_button
        }
        for s in signals:
            try:
                s.disconnect(signals[s])
            except:
                pass
            s.connect(signals[s])

    def show_menu(self):
        self.menu_dock.close() if self.menu_dock else ''
        self.menu_dock = MenuDock(self.iface, self)  
        self.connect_menu_dock_signals()   
        if self.sap_mode:
            self.menu_dock.config_sap_mode()
            profiles_name = self.get_profiles_name()
            self.menu_dock.load({
                'profiles_name' : profiles_name
            })
            self.menu_dock.show_menu()
        else:
            self.postgresql.set_connections_data()
            dbs_name = sorted(self.postgresql.get_dbs_names())
            dbs_name = [u"<Opções>"] + dbs_name
            self.menu_dock.load_dbs_name(dbs_name)
            self.menu_dock.show_menu()

    def get_db_data(self, db_name):
        self.postgresql.load_db_json(db_name, sap_mode=self.sap_mode)
        workspaces_name = sorted(self.postgresql.get_frames_names())
        workspaces_name = [u"Todas"] + workspaces_name
        profiles_name = self.get_profiles_name()
        db_data = {
            'workspaces_name' : workspaces_name,
            'profiles_name' : profiles_name
        }
        return db_data

    def get_profile_data(self, name):
        return self.postgresql.get_menu_profile_data(name)

    def active_button(self, button_data):
        layer_name = button_data['button_data'][u'formValues'][u'*Selecione camada:']
        load_data = LoadData(self.iface)
        if self.sap_mode:
            load_data.sap_mode = self.sap_mode
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            workspace_name = sap_data['unidade_trabalho']
        else:
            workspace_name = button_data['settings_user']['workspace_name']
        layer_vector = load_data.search_layer(layer_name)
        if layer_vector:
            self.classification.run(
                layer_vector,
                button_data
            )
        else:
            self.menu_dock.show_message(
                '''<p style="color: red">A camada "{0}" utilizada por esse botão não está carregada.
                    Carregue a camada!</p>'''.format(layer_name)
            )
        """ result = load_data.load_layers(
            {
                'workspace_name' : workspace_name,
                'style_name' : "",
                'with_geom' : False,
                'layers_name' : [layer_name],
                'rules_name' : [],
                'input_files' : []
            },
            True
        )
        layer_vector = result[0] """

    def open_reclassify_form(self, button_data, layers_selected):
        form = ReclassifyForm()
        form.reclassify.connect(
            self.classification.reclassify
        )
        layer_data = self.get_layer_data(
            button_data['formValues']['*Selecione camada:']
        )
        form.show_form(button_data, layer_data, layers_selected)

    def get_layer_data(self, layer_name):
        return self.postgresql.get_layer_data(layer_name)

    def get_layers_name(self):
        return self.postgresql.get_layers_names()
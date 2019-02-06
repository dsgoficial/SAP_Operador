# -*- coding: utf-8 -*-
from PyQt5 import QtCore
from .menuConfigFrame import MenuConfigFrame
from .menuDock import MenuDock
from .classification import Classification
from .reclassifyForm import ReclassifyForm
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from SAP.managerSAP import ManagerSAP
from Database.postgresql import Postgresql
from Tools.LoadData.loadData import LoadData

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
        
    def get_frame(self):
        profiles_name = self.get_profiles_name()
        options_name = profiles_name + [u"<Novo Perfil>"]
        self.interface_config = MenuConfigFrame(self.iface)
        if self.menu_dock and self.menu_dock.isVisible():
            self.interface_config.setEnabled(True)
        else:
            self.interface_config.setEnabled(False)
        self.interface_config.load({
            'profiles_name' : options_name 
        })
        return self.interface_config

    def get_profiles_name(self):
        db_data = self.postgresql.load_data()
        menu_data = db_data['db_menu']
        profiles_name = [
            menu_data[idx]['nome_do_perfil'] 
            for idx in menu_data
        ]
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']        
            profiles_name = [
                n for n in profiles_name
                if n in sap_data['menus']
            ]
        profiles_name = [u"..."] + profiles_name
        return profiles_name

    def connect_menu_dock_signals(self):
        signals = {
            self.menu_dock.active_button : self.active_button,
            self.menu_dock.load_profile : self.load_profile_selected,
            self.menu_dock.database_load : self.update_dock
        }
        for s in signals:
            try:
                s.disconnect(signals[s])
            except:
                pass
            s.connect(signals[s])

    def show_menu(self):
        self.menu_dock.close() if self.menu_dock else ''
        self.menu_dock = MenuDock(self.iface)  
        self.connect_menu_dock_signals()   
        if self.sap_mode:
            self.menu_dock.config_sap_mode()
            profiles_name = self.get_profiles_name()
            self.menu_dock.load({
                'profiles_name' : profiles_name
            })
            self.menu_dock.show_menu()
        else:
            dbs_name = sorted(self.postgresql.get_dbs_name())
            dbs_name = [u"<Opções>"] + dbs_name
            self.menu_dock.load_dbs_name(dbs_name)
            self.menu_dock.show_menu()

    def update_dock(self, db_name):
        db_data = self.postgresql.load_db_json(db_name)
        workspaces_name = sorted(db_data['db_workspaces_name'])
        workspaces_name = [u"Todas"] + workspaces_name
        profiles_name = self.get_profiles_name()
        self.menu_dock.load({
            'workspaces_name' : workspaces_name,
            'profiles_name' : profiles_name
        })

    def load_profile_selected(self, name):
        db_data = self.postgresql.load_data()
        for idx in db_data['db_menu']:
            if db_data['db_menu'][idx]['nome_do_perfil'] == name:
                profile_data = db_data['db_menu'][idx]
                self.menu_dock.load_menu_profile(profile_data)

    def active_button(self, button_data):
        layer_name = button_data['button_data'][u'formValues'][u'*Selecione camada:']
        db_data = self.postgresql.load_data()
        load_data = LoadData(self.iface)
        if self.sap_mode:
            load_data.sap_mode = self.sap_mode
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            workspace_name = sap_data['unidade_trabalho']
        else:
            workspace_name = button_data['settings_user']['workspace_name']
        result = load_data.load_layers(
            {
                'workspace_name' : workspace_name,
                'style_name' : "",
                'with_geom' : False,
                'layers_name' : [layer_name],
                'rules_name' : [],
                'input_files' : []
            },
            db_data,
            True
        )
        layer_vector = result[0]
        self.classification.run(
            layer_vector,
            button_data
        )

    def open_reclassify_form(self, button_data, layers_selected):
        form = ReclassifyForm()
        form.reclassify.connect(
            self.classification.reclassify
        )
        form.show_form(button_data, layers_selected)
        
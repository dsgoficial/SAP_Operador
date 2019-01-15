# -*- coding: utf-8 -*-
from PyQt5 import QtCore
from .menuConfigFrame import MenuConfigFrame
from .menuDock import MenuDock
from .classification import Classification
from .reclassifyForm import ReclassifyForm
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from Database.postgresql import Postgresql
from Tools.LoadData.loadData import LoadData

class Menu(QtCore.QObject):

    def __init__(self, iface):
        super(Menu, self).__init__()
        self.iface = iface
        self.menu_dock = None
        self.postgresql = Postgresql()
        self.classification = Classification(self.iface)
        self.classification.reclassify_form.connect(
            self.open_reclassify_form
        )

    def get_frame(self):
        db_data = self.postgresql.load_data()
        profiles_name = [db_data['db_menu'][idx]['nome_do_perfil'] for idx in db_data['db_menu']] if db_data else []
        options_name = [u"...", u"<Novo Perfil>"] + sorted(profiles_name) if profiles_name else [""]
        self.interface_config = MenuConfigFrame(self.iface)
        if self.menu_dock and self.menu_dock.isVisible():
            self.interface_config.setEnabled(True)
        else:
            self.interface_config.setEnabled(False)
        self.interface_config.load({
            'profiles_name' : options_name 
        })
        return self.interface_config

    def show_menu(self):
        if not(self.menu_dock):
            self.menu_dock = MenuDock(self.iface)  
            self.menu_dock.start_button.connect(
                self.start_aquisition
            )
        db_data = self.postgresql.load_data()
        self.menu_dock.db_data = db_data
        self.menu_dock.show_menu()

    def start_aquisition(self, button_data):
        layer_name = button_data['button_data'][u'formValues'][u'*Selecione camada:']
        db_data = self.postgresql.load_data()
        settings = {
            'workspace_name' : db_data['settings_user']['workspace_name'],
            'style_name' : "",
            'with_menu' : False,
            'with_geom' : False,
            'layers_name' : [layer_name],
            'rules_name' : [],
            'insumos' : []
        }
        load_data = LoadData(self.iface)
        result = load_data.load_layers(
            settings,
            db_data
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
        
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from .toolsDialog import ToolsDialog
from .LoadData.loadData import LoadData
from .Routines.routines import Routines
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from SAP.managerSAP import ManagerSAP
from utils import cursorWait

class Tools(QtCore.QObject):

    def __init__(self, iface, menu):
        super(Tools, self).__init__()
        self.iface = iface
        self.tool_selected = None
        self.menu = menu
        self.sap_mode = False

    def __del__(self):
        LoadData(self.iface).clean_forms_custom()        

    def show_dialog(self):
        self.interface = ToolsDialog(self.iface)
        self.interface.selected_option.connect(
            self.load_frame
        )
        self.interface.show()
        return self.interface

    def load_frame(self, option_data):
        cursorWait.start()
        choose = option_data['name'] 
        if choose == u"Carregar":
            self.tool_selected = LoadData(self.iface)
            self.tool_selected.sap_mode = self.sap_mode
            self.tool_selected.show_menu.connect(
                self.menu.show_menu
            )
        elif choose == u"Menu":
            self.tool_selected = self.menu
        elif choose == u"Controle" and self.sap_mode:
            self.tool_selected = ManagerSAP(iface=self.iface)
        elif choose == u"Rotinas":
            self.tool_selected = Routines(self.iface)
            self.tool_selected.sap_mode = self.sap_mode
        self.interface.show_frame(
            self.tool_selected.get_frame()
        )
        cursorWait.stop()

    def reload_project_qgis(self):
        LoadData(self.iface).reload_forms_custom()

    
        

    
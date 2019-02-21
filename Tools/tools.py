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

    def __init__(self, iface, menu, sap):
        super(Tools, self).__init__()
        self.iface = iface
        self.tool_selected = None
        self.menu = menu
        self.sap = sap
        self.sap_mode = False
        self.interface = None

    def __del__(self):
        LoadData(self.iface).clean_forms_custom()

    def close_dialog(self):
        if self.interface:
            self.interface.close()
            
    def show_dialog(self):
        self.interface.close() if self.interface else ''  
        self.interface = ToolsDialog(self.iface)
        self.interface.selected_option.connect(
            self.load_frame
        )
        self.interface.show_()
        return self.interface

    def load_frame(self, option_data):
        cursorWait.start()
        try:
            choose = option_data['name'] 
            if choose == u"Dados":
                self.tool_selected = LoadData(self.iface)
                self.tool_selected.sap_mode = self.sap_mode
                self.tool_selected.show_menu.connect(
                    self.menu.show_menu
                )
            elif choose == u"Controle" and self.sap_mode:
                self.tool_selected = self.sap
            elif choose == u"Rotinas":
                self.tool_selected = Routines(self.iface)
                self.tool_selected.sap_mode = self.sap_mode
            self.interface.show_frame(
                self.tool_selected.get_frame()
            )
        finally:
            cursorWait.stop()

    def reload_project_qgis(self):
        LoadData(self.iface).reload_forms_custom()

    
        

    
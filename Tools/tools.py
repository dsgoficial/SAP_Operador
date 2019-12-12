# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from .toolsDialog import ToolsDialog
from .LoadData.loadData import LoadData
from .Routines.routines import Routines
import sys, os
from Ferramentas_Producao.SAP.managerSAP import ManagerSAP
from Ferramentas_Producao.utils import cursorWait

class Tools(QtCore.QObject):

    restart_validate = QtCore.pyqtSignal()

    def __init__(self, iface, menu, sap):
        super(Tools, self).__init__()
        self.iface = iface
        self.tool_selected = None
        self.menu = menu
        self.sap = sap
        self.sap_mode = False
        self.interface = None
        self.sap.close_work.connect(
            self.menu.close_dock
        )
        self.loadData = LoadData(self.iface)
        self.loadData.restart_validate.connect(
            self.restart_validate.emit
        )
        self.loadData.show_menu.connect(
            self.menu.show_menu
        )
        self.routines = Routines(self.iface)

    def __del__(self):
        LoadData(self.iface).clean_forms_custom()

    def close_dialog(self):
        if self.interface:
            self.interface.close()
            
    def show_dialog(self):
        self.interface = ToolsDialog(self.iface)
        self.interface.selected_option.connect(
            self.load_frame
        )
        if self.sap_mode:
            self.loadData.sap_mode = self.sap_mode
            self.loadData.update_frame()
            self.interface.controller_btn.click()
            self.loadData.hasMenu = self.menu.load_data()
        else:
            self.loadData.sap_mode = self.sap_mode
            #self.loadData = LoadData(self.iface)
            self.interface.controller_btn.setVisible(False)
            self.interface.load_btn.click()
        self.interface.show_()
        return self.interface

    def load_frame(self, option_data):
        cursorWait.start()
        try:
            choose = option_data['name'] 
            if choose == u"controller_btn":
                self.tool_selected = self.sap
            elif choose == u"rotines_btn":
                self.tool_selected = self.routines
                self.tool_selected.sap_mode = self.sap_mode
            else:
                self.tool_selected = self.loadData
            self.interface.show_frame(
                self.tool_selected.get_frame()
            )
        finally:
            cursorWait.stop()

    def reload_project_qgis(self):
        LoadData(self.iface).reload_forms_custom()

    
        

    
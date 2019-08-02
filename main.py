# -*- coding: utf-8 -*-

import os, sys
from qgis import core, gui
from PyQt5 import QtCore
from .SAP.managerSAP import ManagerSAP
from .Tools.tools import Tools
from .Tools.Menu.menu import Menu
from .Validate.validateOperations import ValidateOperations
from .utils.managerQgis import ManagerQgis
from .utils.messageSave import MessageSave

class Main(QtCore.QObject):
    def __init__(self, iface):
        super(Main, self).__init__()
        self.iface = iface
        self.sap = ManagerSAP(self.iface)
        self.menu = Menu(self.iface)
        self.validate = ValidateOperations(self.iface)
        self.tools = Tools(self.iface, self.menu, self.sap)
        self.msg_save = MessageSave(self.iface,30)#5*60)

    def initGui(self):
        self.sap.add_action_qgis(True)
        self.sap.show_tools.connect(
            self.show_tools_dialog
        )
        self.sap.close_tools.connect(
            self.tools.close_dialog
        )
        core.QgsProject.instance().readProject.connect(
            self.load_qgis_project
        )
        ManagerQgis(self.iface).load_custom_config()
        
    def unload(self):
        self.sap.add_action_qgis(False)
        self.sap.show_tools.disconnect(
            self.show_tools_dialog
        )
        self.sap.close_tools.disconnect(
            self.tools.close_dialog
        )
        del self.tools
        core.QgsProject.instance().readProject.disconnect(
            self.load_qgis_project
        )
        self.validate.stop()
        del self.sap
        del self.validate

    def load_qgis_project(self):
        value = ManagerQgis(self.iface).load_project_var("settings_user")
        if value:
            self.msg_save.start() if not(self.msg_save.is_running) else ''
            self.tools.reload_project_qgis()
            self.validate.start()
            
    def closed_tools_dialog(self):
        self.sap.enable_action_qgis(True)
        self.validate.restart()
                
    def show_tools_dialog(self, sap_mode):
        self.sap.enable_action_qgis(False)
        self.menu.sap_mode = sap_mode
        self.tools.sap_mode = sap_mode
        self.tools.show_dialog().closed_tools_dialog.connect(
            self.closed_tools_dialog 
        )
        self.msg_save.start() if not(self.msg_save.is_running) else ''


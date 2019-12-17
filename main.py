# -*- coding: utf-8 -*-

import os, sys
from qgis import core, gui
from PyQt5 import QtCore
from Ferramentas_Producao.SAP.managerSAP import ManagerSAP
from Ferramentas_Producao.Tools.tools import Tools
from Ferramentas_Producao.Tools.Menu.menu import Menu
from Ferramentas_Producao.Validate.validateOperations import ValidateOperations
from Ferramentas_Producao.utils.managerQgis import ManagerQgis
from Ferramentas_Producao.utils.messageSave import MessageSave
from Ferramentas_Producao.Microcontroller.monitoring import Monitoring

class Main(QtCore.QObject):
    def __init__(self, iface):
        super(Main, self).__init__()
        self.plugin_dir = os.path.dirname(__file__)
        self.iface = iface
        self.sap = ManagerSAP(self.iface)
        self.menu = Menu(self.iface)
        self.validate = ValidateOperations(self.iface)
        self.tools = Tools(self.iface, self.menu, self.sap)
        self.msg_save = MessageSave(self.iface, 1000*150)
        self.sap_mode = False
        self.monitoring = Monitoring(self.iface)

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
        self.iface.actionNewProject().triggered.connect(
            self.new_qgis_project
        )
        self.mQ = ManagerQgis(self.iface)
        self.mQ.load_custom_config()
        
    def unload(self):
        self.sap.add_action_qgis(False)
        try:
            self.sap.show_tools.disconnect(
                self.show_tools_dialog
            )
        except:
            pass
        try:
            self.sap.close_tools.disconnect(
                self.tools.close_dialog
            )
        except:
            pass
        del self.tools
        try:
            core.QgsProject.instance().readProject.disconnect(
                self.load_qgis_project
            )
        except:
            pass
        try:
            self.iface.actionNewProject().triggered.disconnect(
                self.new_qgis_project
            )
        except:
            pass
        self.validate.stop()
        self.monitoring.stopCanvas()
        del self.sap
        del self.validate
        del self.monitoring
        self.mQ.delete_shortcut_actions()

    def load_qgis_project(self):
        value = ManagerQgis(self.iface).load_project_var("settings_user")
        if value:
            self.msg_save.start() if not(self.msg_save.is_running) else ''
            self.tools.reload_project_qgis()
            self.validate.start()

    def new_qgis_project(self):
        self.monitoring.stopCanvas()
            
    def closed_tools_dialog(self):
        self.sap.enable_action_qgis(True)

    def restart_validate(self):
        if self.sap_mode:
            self.validate.restart()
                
    def show_tools_dialog(self, sap_mode, activeMonitoring):
        self.monitoring.startCanvas() if activeMonitoring else self.monitoring.stopCanvas()
        self.sap_mode = sap_mode
        self.sap.enable_action_qgis(False)
        self.menu.sap_mode = sap_mode
        self.tools.sap_mode = sap_mode
        self.tools.restart_validate.connect(
            self.restart_validate
        )
        self.tools.show_dialog().closed_tools_dialog.connect(
            self.closed_tools_dialog 
        )
        self.msg_save.start() if not(self.msg_save.is_running) else ''


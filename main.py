# -*- coding: utf-8 -*-

import os, sys
from qgis import core, gui
from PyQt5 import QtCore
from .Login.login import Login
from .Tools.tools import Tools
from .Tools.Menu.menu import Menu
from .Validate.validateOperations import ValidateOperations

class Main(QtCore.QObject):
    def __init__(self, iface):
        super(Main, self).__init__()
        self.iface = iface
        self.login = Login(self.iface)
        self.menu = Menu(self.iface)
        self.validate = ValidateOperations(self.iface)
        self.tools = Tools(self.iface, self.menu)

    def initGui(self):
        self.login.action.add_on_qgis()
        self.login.show_tools.connect(
            self.show_tools_dialog
        )
        core.QgsProject.instance().readProject.connect(
            self.load_qgis_project
        )
        
    def unload(self):
        del self.tools
        self.login.action.remove_from_qgis()
        self.login.show_tools.disconnect(
            self.show_tools_dialog
        )
        core.QgsProject.instance().readProject.disconnect(
            self.load_qgis_project
        )
        del self.login
        self.validate.stop()
        del self.validate

    def load_qgis_project(self):
        self.validate.start()
                
    def show_tools_dialog(self):
        self.login.action.setEnabled(False)
        self.tools.show_dialog().enable_action.connect(
            lambda : self.login.action.setEnabled(True)
        )



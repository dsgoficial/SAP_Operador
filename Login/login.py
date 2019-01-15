# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from .loginAction import LoginAction
from .loginDialog import LoginDialog
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import managerQgis

class Login(QtCore.QObject):

    show_tools = QtCore.pyqtSignal()

    def __init__(self, iface):
        super(Login, self).__init__()
        self.iface = iface
        self.action = LoginAction(self.iface)
        self.action.show_login_dialog.connect(
            self.show_login_dialog
        )

    def login_remote(self, login_data):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.interface.accept()
        del self.interface
        managerQgis.save_qsettings_var('login/server', login_data['server'])
        managerQgis.save_project_var('user', login_data['user'])
        managerQgis.save_project_var('password', login_data['password'])
        print(login_data)
        #self.show_tools.emit()
        QtWidgets.QApplication.restoreOverrideCursor()
    
    def login_local(self, login_data):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.interface.accept()
        del self.interface
        self.show_tools.emit()
        QtWidgets.QApplication.restoreOverrideCursor()

    def show_login_dialog(self):
        self.interface = LoginDialog(self.iface)
        server = managerQgis.load_qsettings_var('login/server')
        user = managerQgis.load_project_var('user')
        password = managerQgis.load_project_var('password')
        self.interface.load_login_data(server, user, password)
        self.interface.login_local.connect(
            self.login_local
        )
        self.interface.login_remote.connect(
            self.login_remote
        )
        self.interface.show()
        
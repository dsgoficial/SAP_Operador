# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from .loginAction import LoginAction
from .loginDialog import LoginDialog
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import managerQgis, msgBox
from SAP.managerSAP import ManagerSAP

class Login(QtCore.QObject):

    show_tools = QtCore.pyqtSignal(bool)

    def __init__(self, iface):
        super(Login, self).__init__()
        self.iface = iface
        self.action = LoginAction(self.iface)
        self.action.show_login_dialog.connect(
            self.show_login_dialog
        )
    
    def login_local(self, login_data):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.dialog.accept()
        del self.dialog
        self.show_tools.emit(False)
        QtWidgets.QApplication.restoreOverrideCursor()

    def login_remote(self, login_data):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        server = login_data['server']
        user = login_data['user']
        password = login_data['password']
        managerQgis.save_qsettings_var('login/server', server)
        managerQgis.save_project_var('user', user)
        managerQgis.save_project_var('password', password)
        sap = ManagerSAP(parent=self.dialog)
        sucess = sap.login(server, user, password)
        if sucess:
            self.dialog.accept()
            del self.dialog
            self.show_tools.emit(True)
        QtWidgets.QApplication.restoreOverrideCursor()

    def show_login_dialog(self):
        self.dialog = LoginDialog(self.iface)
        server = managerQgis.load_qsettings_var('login/server')
        user = managerQgis.load_project_var('user')
        password = managerQgis.load_project_var('password')
        self.dialog.load_login_data(server, user, password)
        self.dialog.login_local.connect(
            self.login_local
        )
        self.dialog.login_remote.connect(
            self.login_remote
        )
        self.dialog.show()
        
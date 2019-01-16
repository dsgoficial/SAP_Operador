# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from .loginAction import LoginAction
from .loginDialog import LoginDialog
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import managerQgis, network, msgBox

class Login(QtCore.QObject):

    show_tools = QtCore.pyqtSignal(dict)

    def __init__(self, iface):
        super(Login, self).__init__()
        self.iface = iface
        self.action = LoginAction(self.iface)
        self.action.show_login_dialog.connect(
            self.show_login_dialog
        )
    
    def login_local(self, login_data):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.interface.accept()
        del self.interface
        self.show_tools.emit({})
        QtWidgets.QApplication.restoreOverrideCursor()

    def login_remote(self, login_data):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        managerQgis.save_qsettings_var('login/server', login_data['server'])
        managerQgis.save_project_var('user', login_data['user'])
        managerQgis.save_project_var('password', login_data['password'])
        response = self.logon_sap(login_data)
        if response:
            self.interface.accept()
            del self.interface
            self.show_tools.emit(response)
        QtWidgets.QApplication.restoreOverrideCursor()

    def logon_sap(self, login_data):
        net = network
        net.CONFIG['parent'] = self.interface
        post_data = {
            u"usuario" : login_data['user'],
            u"senha" : login_data['password']
        }
        server = login_data['server']
        url = u"{0}/login".format(server)
        response = net.POST(server, url, post_data)
        if response and response.json()['sucess']:
            token = response.json()['dados']['token']
            header = {'authorization' : token}
            url = u"{0}/distribuicao/verifica".format(server)
            response = net.GET(server, url, header)
            if response:
                data = response.json()
                if "dados" in data:
                    data['token'] = token
                    return data
                else:
                    return self.init_activity(server, token)
        return False
    
    def init_activity(self, server, token):
        net = network
        net.CONFIG['parent'] = self.interface
        result = self.interface.show_message("new activity")
        if result == 16384:
            header = {'authorization' : token}
            url = u"{0}/distribuicao/inicia".format(server)
            response = net.POST(server, url, header=header)
            data = response.json()
            if data['sucess']:
                data['token'] = token
                return data
            self.interface.show_message("no activity")

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
        
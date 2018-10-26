# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui, utils
import json, sys, os, copy, base64
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from managerQgis.projectQgis import ProjectQgis
from login.login import Login

class Project(QtCore.QObject):

    def __init__(self, iface, dataLogin=False):
        super(Project, self).__init__()
        self.iface = iface

    def encrypt(self, key, plaintext):
        return base64.b64encode(plaintext)

    def decrypt(self, key, ciphertext):
        return base64.b64decode(ciphertext)

    def validate(self):
        lg = Login(self.iface)
        self.projectQgis = ProjectQgis(self.iface)
        user = self.projectQgis.getVariableProject('usuario')
        password = self.projectQgis.getVariableProject('senha')
        task = self.projectQgis.getVariableProject('atividade')
        server = lg.serverLineEdit.text()
        if user and password and task and server:
            user = self.decrypt('123456', user)
            password = self.decrypt('123456', password)
            current_task = self.decrypt('123456', task)
            data, status_code = lg.checkLogin(server, user, password)
            if data and "dados" in data:
                different_projects = data['dados']['atividade']['nome'] != current_task.decode('utf-8')
                if different_projects:
                    core.QgsMapLayerRegistry.instance().removeAllMapLayers()
                    core.QgsProject.instance().layerTreeRoot().removeAllChildren()
                    QtGui.QMessageBox.critical(
                        self.iface.mainWindow(),
                        u"Aviso", 
                        u"<p>Esse projeto não pode ser acessado. Carregue um novo projeto.</p>"
                    )
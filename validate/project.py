# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSettings
from qgis import core, gui, utils
import json, sys, os, copy
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from managerQgis.projectQgis import ProjectQgis
from login.login import Login

class Project(QtCore.QObject):

    def __init__(self, iface, dataLogin=False):
        super(Project, self).__init__()
        self.iface = iface
        self.projectQgis = ProjectQgis(self.iface)

    def validate(self):
        user = self.projectQgis.getVariableProjectEncrypted('usuario')
        password = self.projectQgis.getVariableProjectEncrypted('senha')
        task = self.projectQgis.getVariableProjectEncrypted('atividade').decode('utf-8')
        settings = QSettings()
        settings.beginGroup('SAP/server')
        server = settings.value('server')
        if user and password and task and server:
            lg = Login(self.iface)
            data, status_code = lg.checkLogin(server, user, password)
            if not data or "dados" not in data or data['dados']['atividade']['nome'] != task:
                core.QgsMapLayerRegistry.instance().removeAllMapLayers()
                core.QgsProject.instance().layerTreeRoot().removeAllChildren()
                QtGui.QMessageBox.critical(
                    self.iface.mainWindow(),
                    u"Aviso", 
                    u"<p>Esse projeto não pode ser acessado. Carregue um novo projeto.</p>"
                )
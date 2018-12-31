# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui
import resources
from login.login import Login
from mainInterface.tools import Tools
from managerLoadLayers.loadLayers import LoadLayers
from menu.menu_functions import Menu_functions
from managerQgis.projectQgis import ProjectQgis
from managerQgis.messageSave import MessageSave
from managerNetwork.network import Network
from trackLayers.track import Track
from validate.addFeatures import AddFeatures
from validate.geometryChanged import GeometryChanged
from validate.project import Project
from custom_action import ActionTest


class Main:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.tools = None
        self.data = {}
        self.menu_functions = None
        self.projectQgis = None
        self.track_lyrs = None
        self.validate_add_feat = None
        self.msg_save = MessageSave(self.iface)
        
    def addActionOnQgis(self):
        self.action = ActionTest(self.iface)
        self.iface.digitizeToolBar().addAction(self.action)
        self.action.triggered.connect(
            self.showLogin
        )
    
    def showLogin(self):
        if not(self.tools and self.tools.isVisible()):
            self.login = Login(self.iface)
            self.login.showTools.connect(
                self.showTools
            )
            self.login.exec_()
    
    def finishActivity(self):
            unitId = self.data["dados"]["atividade"]["unidade_trabalho_id"]
            faseId = self.data["dados"]["atividade"]["subfase_etapa_id"]
            server = self.data["server"]
            token = self.data["token"]
            user = self.data["user"] 
            password = self.data["password"]
            self.net = Network()
            code = self.login.finishActivity(server, unitId, faseId, token)
            if code == 500:
                QtGui.QMessageBox.critical(
                    self.tools,
                    "ERRO:", 
                    u"<p style='color: red;'>\
                    Erro: Não foi possível finalizar essa atividade.\
                    </p>"
                ) 
            else:
                self.iface.actionNewProject().trigger()
                self.tools.removeAllActivity()
                self.tools.close()
                self.menu_functions.closeMenuClassification()
                self.login.loginRemote(user, password, server)  

    def showTools(self, dataLogin):
        self.data = dataLogin
        self.tools = Tools(self.iface)
        self.track_layers()
        self.msg_save.start() if not(self.msg_save.isRunning) else ''
        self.menu_functions.tools = self.tools
        self.menu_functions.data = self.data
        self.tools.menu_functions = self.menu_functions
        self.tools.data = dataLogin
        self.tools.parent = self
        self.tools.show()

    def track_layers(self):
        if not(self.track_lyrs):
            self.track_lyrs = Track(self.iface)
            self.init_validates_feat()

    def init_validates_feat(self):
        self.validate_add_feat = AddFeatures(self.iface)
        self.track_lyrs.layerModified.connect(self.validate_add_feat.validate)
        self.validate_geom_change = GeometryChanged(self.iface)
        self.track_lyrs.layerModified.connect(self.validate_geom_change.validate)
        

    def removeActionFromQgis(self):
        self.iface.digitizeToolBar().removeAction(self.action)
        del self.action

    def cleanFormsCustom(self):
        loadLayers = LoadLayers(self.iface, {})
        loadLayers.cleanDirectoryUI()

    def loadProject(self):
        prj = Project(self.iface)
        prj.validate()
        loadLayers = LoadLayers(self.iface, {})
        loadLayers.reloadFormsCustom()
        self.menu_functions.showMenuClassification()
        self.track_layers()
        self.msg_save.start() if not(self.msg_save.isRunning) else ''

    def initGui(self):
        self.addActionOnQgis()
        core.QgsProject.instance().readProject.connect(
            self.loadProject
        )
        self.menu_functions = Menu_functions(self.iface, self.data) 
        self.projectQgis = ProjectQgis(self.iface)
        self.projectQgis.configShortcut()
        
                
    def unload(self):
        self.removeActionFromQgis()
        try:
            core.QgsProject.instance().readProject.disconnect(
                self.loadProject
            )
        except:
            pass
        del self.projectQgis
        self.cleanFormsCustom()
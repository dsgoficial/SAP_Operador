#! -*- coding: UTF-8 -*-
from PyQt4 import QtGui, QtCore
from qgis import core
import sys, json, copy, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from database.postgresql_v2 import Postgresql_v2
from managerQgis.projectQgis import ProjectQgis
from menu_interface import Menu_interface
from menu_forms import Menu_forms
from classification import Classification

class Menu_functions(QtCore.QObject):
    def __init__(self, iface, data, tools=False):
        super(Menu_functions, self).__init__() 
        self.iface = iface
        self.data = data
        self.tools = tools
        self.menu_interface = Menu_interface(self.iface, self)
        self.menu_forms = None

    def getDbName(self):
        if self.data:  
            return self.data["dados"]["atividade"]["banco_dados"]["nome"]
        elif self.tools and self.tools.getDbName() and u"<Opções>" != self.tools.getDbName():
            return self.tools.getDbName() 
        return ProjectQgis(self.iface).getVariableProject('dbname')

    def getStyleName(self):
        if self.tools and self.tools.getStyleName():
            return self.tools.getStyleName() 
        return ProjectQgis(self.iface).getVariableProject('stylename')

    def getWorkspaceName(self):
        if self.data:          
            return self.data["dados"]["atividade"]["unidade_trabalho"]
        elif self.tools and self.tools.getWorkspace():
            return self.tools.getWorkspace() 
        return ProjectQgis(self.iface).getVariableProject('workspace') 

    def getPostgresql(self):
        postgresql = Postgresql_v2(self.iface)
        if self.data:
            postgresql.modeRemote = True
            postgresql.geom = self.data["dados"]["atividade"]["geom"]
            postgresql.connectPsycopg2WithLoginData({
                "user" : self.data["user"],
                "password" : self.data["password"],
                "host" : self.data["dados"]["atividade"]["banco_dados"]["servidor"],
                "port" : self.data["dados"]["atividade"]["banco_dados"]["porta"],
                "dbname" : self.data["dados"]["atividade"]["banco_dados"]["nome"]
            })
        else:
            dbName = self.getDbName()         
            postgresql.connectPsycopg2(dbName)
        return postgresql
   
    def exportDataMenuOnProject(self):
        dbName = self.getDbName()  
        styleName = self.getStyleName()
        workspaceName = self.getWorkspaceName()
        if dbName and dbName != u"<Opções>" and styleName and workspaceName:
            profile = self.getProfileMenu()
            orderMenu = self.getOrderMenu()
            projectQgis = ProjectQgis(self.iface)
            projectQgis.setProjectVariable('dbname', dbName)
            projectQgis.setProjectVariable('stylename', styleName)
            projectQgis.setProjectVariable('workspace', workspaceName)
            if profile:
                projectQgis.setProjectVariable(
                    'profile', 
                    json.dumps(copy.deepcopy(profile))
                )
                projectQgis.setProjectVariable(
                    'orderMenu', 
                    json.dumps(copy.deepcopy(orderMenu))
                )
            return True 
        return False

    def getProfileMenu(self):
        if self.tools and self.tools.profile:
            return self.tools.profile 
        return json.loads(ProjectQgis(self.iface).getVariableProject('profile', isJson=True)) 
    
    def getOrderMenu(self):
        if self.tools and self.tools.orderMenu:
            return self.tools.orderMenu 
        return json.loads(ProjectQgis(self.iface).getVariableProject('orderMenu', isJson=True)) 

    def closeMenuClassification(self):
        self.menu_interface.close()
        
    def showMenuClassification(self):
        self.exportDataMenuOnProject()
        self.menu_interface.tabWidget.cleanAllTabWidget()
        self.menu_interface.loadMenu(
            self.getOrderMenu(),
            self.getProfileMenu() 
        )
        self.iface.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.menu_interface )

    def startClassification(self, button, activeReclass):
        postgresql = self.getPostgresql()
        self.classification = Classification(
            self.iface, 
            self.data,
            postgresql.dbJson
        )
        self.classification.run(
            button, 
            activeReclass,
            postgresql.getConnectionData(),
            {
                'dbname' : self.getDbName(),
                'stylename' : self.getStyleName(),
                'workspace' : self.getWorkspaceName(),
            }
        )
    
    def cleanMenuData(self):
        projectQgis = ProjectQgis(self.iface)
        if self.tools:
            self.tools.profile = None 
            self.tools.orderMenu = None
        projectQgis.setProjectVariable(
            "orderMenu", 
            ""
        )
        projectQgis.setProjectVariable(
            "profile", 
            ""
        )
        projectQgis.setProjectVariable(
            "loginData", 
            ""
        )

    def updateMenuData(self, tabwidget, profile):
        projectQgis = ProjectQgis(self.iface)
        orderMenu = tabwidget.getOrderMenu()
        self.tools.orderMenu = tabwidget.getOrderMenu()
        projectQgis.setProjectVariable(
            "orderMenu", 
            json.dumps(copy.deepcopy(orderMenu))
        )
        self.tools.profile = profile
        projectQgis.setProjectVariable(
            "profile", 
            json.dumps(copy.deepcopy(profile))
        )
    
    def updateCurrentForm(self):
        if self.tools.vLayoutMenuForm.count() != 0:
            self.tools.currentFormMenu.deleteLater() if self.tools.currentFormMenu else ''
        self.tools.currentFormMenu = self.menu_forms
        self.tools.vLayoutMenuForm.addWidget(self.menu_forms)

    def showFormAddTabMenu(self):
        self.menu_forms = Menu_forms()
        self.menu_forms.ok.connect(
            self.menu_interface.createTab        
        )
        self.menu_forms.createAddTabForm() 
        self.updateCurrentForm()
    
    def showEditTabMenu(self):
        self.menu_forms = Menu_forms()
        self.menu_forms.ok.connect(
            self.menu_interface.editTab        
        )
        self.menu_forms.createEditTabForm(self.menu_interface.tabWidget) 
        self.updateCurrentForm()
                    
    def showFormDelTabMenu(self):
        self.menu_forms = Menu_forms()
        self.menu_forms.ok.connect(
            self.menu_interface.removeTab        
        )
        self.menu_forms.createDelTabForm(
            self.menu_interface.tabWidget.getAllNamesTabs().keys()
        )
        self.updateCurrentForm()
        
    def showFormAddButtonMenu(self):
        self.menu_forms = Menu_forms()
        self.menu_forms.ok.connect(
            self.menu_interface.addButtonMenu        
        )
        postgresql = self.getPostgresql()
        self.menu_forms.createAddButtonForm(
            self.getDbName(),
            postgresql.dbJson,
            self.menu_interface.tabWidget.getAllNamesTabs().keys()
        )
        self.updateCurrentForm()
                          
    def showFormDelButtonMenu(self):
        self.menu_forms = Menu_forms()
        self.menu_forms.ok.connect(
            self.menu_interface.removeButtonLayer        
        )
        self.menu_forms.createDelButtonForm(
           self.menu_interface.tabWidget
        )
        self.updateCurrentForm()

    def showFormSaveProfileOnDb(self):
        self.menu_forms = Menu_forms()
        self.menu_forms.ok.connect(
            self.saveProfileOnDb        
        )
        self.menu_forms.createSaveProfileOnDbForm()
        self.updateCurrentForm()
    
    def showFormLoadProfileOnFile(self):
        self.menu_forms = Menu_forms()
        self.menu_forms.ok.connect(
            self.loadProfileFromFile        
        )
        self.menu_forms.createLoadProfileFromFileForm()
        self.updateCurrentForm()

    def loadProfileFromFile(self, formValues, fields):
        fileOrigin = open(formValues[u'*Selecion o arquivo com o perfil:'], "r") 
        data = fileOrigin.read()
        profileData = json.loads(data)
        self.tools.profile = profileData['perfil']
        self.tools.orderMenu = profileData['orderMenu']
        self.showMenuClassification()
        QtGui.QMessageBox.information(
            self.tools,
            u"Aviso:", 
            u"Perfil carregado!"
        )

    def showFormSaveProfileOnFile(self):
        profileData = self.tools.profiles
        if profileData:
            profiles = [ profileData[i]['nome_do_perfil'] for i in profileData]
            profileSelected = str(self.tools.getProfileNameSelected())
            self.menu_forms = Menu_forms()
            self.menu_forms.ok.connect(
                self.saveProfileOnFile        
            )
            self.menu_forms.createSaveProfileOnFileForm(profiles, profileSelected)
            self.updateCurrentForm()

    def validateValuesForm(self, formValues):
        for key in formValues:
            if u"*" in key and not(formValues[key]):
                QtGui.QMessageBox.information(
                    self.tools,
                    u"Aviso:", 
                    u"Todos os campos com '*' são obrigatório"
                )
                return False
        return True

    def saveProfileOnFile(self, formValues, fields):
        if self.validateValuesForm(formValues):
            pathDest = os.path.join(
                formValues[u'*Selecion uma pasta para salvar o arquivo:'],
                "{0}.json".format(formValues[u'*Informe o nome do Arquivo:'])
            )
            profileName = formValues[u'Selecione o perfil do menu:']
            profileData = self.tools.profileData
            for i in profileData:
                if profileName == profileData[i]['nome_do_perfil']:
                    fileDest = open(pathDest, "w") 
                    data = json.dumps(
                        {
                            'perfil' : profileData[i]['perfil'],
                            'orderMenu' : profileData[i]['orderMenu']
                        }, 
                        indent=4
                    )
                    fileDest.write(data)
                    fileDest.close()
                    QtGui.QMessageBox.information(
                        self.tools,
                        u"Aviso:", 
                        u"Arquivo salvo!"
                    )

    def saveProfileOnDb(self, formValues, fields):
        dbname = self.getDbName()
        profile = self.getProfileMenu()
        orderMenu = self.getOrderMenu()
        profileName = formValues[u'*Informe o nome do perfil:']
        postgresql = self.getPostgresql()
        postgresql.saveProfile({ 
                'dbName' : dbname,
                'profile' : profile,
                'profileName' : profileName,
                'orderMenu' : orderMenu
        })
        QtGui.QMessageBox.information(
            self.tools,
            "Aviso:", 
            "Perfil salvo com sucesso!"
        )
        if self.tools:
            self.tools.loadProfileGroupBox()
            self.tools.profiles = self.tools.getProfilesDataFormated()

    def showEditAttributesShortcutButton(self, button):
        self.menu_forms = Menu_forms()
        self.menu_forms.ok.connect(
            button.finishEditAttributes        
        )        
        buttonName = button.objectName()
        try:
            button.editedButtonData.disconnect(self.editButtonData)
        except:
            pass
        button.editedButtonData.connect(self.editButtonData)
        self.menu_forms.createEditButtonShortcutForm(button)
        self.menu_forms.exec_()
    
    def editButtonData(self, buttonNameOld, button):
        buttonNameNew = button.objectName()
        tabName = button.buttonData['formValues'][u'*Selecione aba:']
        profile = self.getProfileMenu()
        del profile[unicode(tabName)][unicode(buttonNameOld)]
        profile[unicode(tabName)][unicode(buttonNameNew)] = button.buttonData 
        ProjectQgis(self.iface).setProjectVariable(
            "profile", 
            json.dumps(copy.deepcopy(profile), ensure_ascii=False).encode('utf8')
        )

    def showEditAttributesButton(self):
        self.menu_forms = Menu_forms()
        self.menu_forms.ok.connect(
            self.menu_interface.editButtonAttributes        
        )
        self.menu_forms.createEditButtonForm(self.menu_interface.tabWidget)
        self.updateCurrentForm()



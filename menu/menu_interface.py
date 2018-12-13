#! -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import gui, core
from menu_button import Menu_button
from menu_tabWidget import Menu_tabWidget
from menu_forms import Menu_forms
import copy, json

class Menu_interface(QtGui.QDockWidget):

    def __init__(self, iface, menu_functions):
        super(Menu_interface, self).__init__()
        self.iface = iface
        self.menu_functions = menu_functions
        self.dockWidgetContents = QtGui.QWidget()
        self.setWindowTitle(u"Menu de classificação")
        #criar layout principal do menu
        layoutMenu = QtGui.QVBoxLayout(self.dockWidgetContents)
        #cria checkBox reclassificação
        configFrame = QtGui.QFrame(self.dockWidgetContents)
        configLayout = QtGui.QVBoxLayout(configFrame)
        self.reclassificationCheckBox = QtGui.QCheckBox(
            u'Ativar reclassificação',
            configFrame 
        )
        configLayout.addWidget(self.reclassificationCheckBox)
        layoutMenu.addWidget(configFrame)
        #cria tabwidget do menu
        self.tabWidget = Menu_tabWidget(self.dockWidgetContents)
        layoutMenu.addWidget(self.tabWidget)
        #cria pesquisa do menu
        searchLayout = QtGui.QHBoxLayout()
        searchLabel = QtGui.QLabel(self.dockWidgetContents)
        searchLabel.setText(u"Pesquisa :")
        searchLayout.addWidget(searchLabel)
        self.searchByName = QtGui.QLineEdit(self)
        self.searchByName.mousePressEvent = lambda _:self.searchByName.selectAll()
        searchLayout.addWidget(self.searchByName)
        layoutMenu.addLayout(searchLayout)
        self.setWidget(self.dockWidgetContents)
        self.filterByNameList = []
        self.currentButtonMenu = None
        self.sClassification = False

    def showEvent(self, e):
        self.connectSignals()

    def closeEvent(self, e):
        self.disconnectSignals()
        self.cleanMenu()
    
    def connectSignals(self):
        self.searchByName.textEdited.connect(
            self.filterButtonMenuByName
        )
        
    def disconnectSignals(self):
        try:
            self.searchByName.textEdited.disconnect(
                self.filterButtonMenuByName
            )
        except:
            pass

    def loadMenu(self, orderMenu, profile):
        if profile:
            for tabName in reversed(orderMenu["orderTab"]):
                if tabName in profile:
                    self.tabWidget.addTabs(tabName)
                    for buttonName in orderMenu["orderButton"][tabName]:
                        if buttonName in profile[tabName]:
                            buttonData = profile[tabName][buttonName]
                            self.createButton(buttonData)
            self.addTabSearch(profile)
            return True

    def addTabSearch(self, profile):
        self.tabWidget.addTabs(u'**Pesquisa**')
        for tabName in profile:
            for buttonName in profile[tabName]:
                buttonData = copy.deepcopy(
                    profile[tabName][buttonName]
                ) 
                buttonData['formValues'][u'*Selecione aba:'] = u'**Pesquisa**'
                self.createButton(buttonData)
        
    def cleanMenu(self):
        self.tabWidget.cleanAllTabWidget()
        self.menu_functions.cleanMenuData()
        self.iface.removeDockWidget(self)
        
    def createTab(self, formValues, fields):
        nameTab = formValues[u'Nome da aba:']
        profile = self.menu_functions.getProfileMenu()
        if  not nameTab in profile:
            self.tabWidget.addTabs(nameTab)
            profile[nameTab] = {}
            self.addTabSearch(profile)
            self.menu_functions.updateMenuData(self.tabWidget, profile)
        else:
            QtGui.QMessageBox.information(
                self.iface.mainWindow(),
                "Aviso:", 
                u"<p style='color: red;'>\
                Erro: Não pode existir mais de uma aba com o mesmo nome.\
                </p>\
                <p style='color: blue;'>\
                Solução: Escolha outro nome para sua aba.\
                </p>"
            ) 
    
    def editTab(self, formValues, fields):
        tabs = fields
        tabOld = formValues[u'*Selecione a aba:']
        if  tabOld in fields:
            profile = self.menu_functions.getProfileMenu()
            dataBKP = profile[tabOld]
            del profile[tabOld]
            tabNew = formValues[u'*Novo nome para aba:']
            self.tabWidget.setTabText(tabs[tabOld], tabNew)
            profile[tabNew] = dataBKP
            for buttonName in profile[tabNew]:
                profile[tabNew][buttonName]['formValues'][u'*Selecione aba:'] = tabNew
            self.menu_functions.updateMenuData(self.tabWidget, profile)
        else:
            QtGui.QMessageBox.information(
                self.iface.mainWindow(),
                "Aviso:", 
                u"<p style='color: red;'>\
                Erro: Os campos obrigatórios (*) não foram preenchido.\
                </p>\
                <p style='color: blue;'>\
                Solução: Preencha os campos obrigatórios e tente novamente.\
                </p>"
            )

    def removeTab(self, formValues, fields):
        tabName =  formValues['Selecione Aba para remover:']
        self.tabWidget.removeTabByName(tabName)
        profile = self.menu_functions.getProfileMenu()
        if tabName in profile:
            del  profile[tabName]
        self.addTabSearch(profile)
        self.menu_functions.updateMenuData(self.tabWidget, profile)

    def addButtonMenu(self, formValues, fields):
        if self.validateAddButton(formValues):
            buttonName = formValues[u'*Nome do botão:']
            tabName = formValues[u'*Selecione aba:']
            buttonData = {
                'formValues' : copy.deepcopy(formValues),
                'fields' : copy.deepcopy(fields),
            }
            self.createButton(buttonData)
            profile = self.menu_functions.getProfileMenu()
            profile[tabName][buttonName] = buttonData
            self.addTabSearch(profile)
            self.menu_functions.updateMenuData(self.tabWidget, profile)
        else:
            QtGui.QMessageBox.information(
            self.iface.mainWindow(),
                "Aviso:", 
                u"<p style='color: red;'>\
                Erro: Não pode existir mais de um botão com o mesmo nome\
                ou com o nome em branco;\
                </p>\
                <p style='color: blue;'>\
                Solução: Informe ou escolha outro nome para seu botão.\
                </p>"
            )

    def createButton(self, buttonData):
        button = self.tabWidget.addButtonLayer(buttonData)
        button.run.connect(self.runButtonMenu)
        button.openForm.connect(
            self.menu_functions.showEditAttributesShortcutButton
        ) 

    def runButtonMenu(self, button):
        self.tabWidget.reloadStandardStylesButtons()
        styles = {
            'a' : "color: rgb(255, 255, 255);\
                   background-color: rgb(255, 128, 0);", 
            'c' : "background-color: rgb(255, 128, 0);",
            'p' : "color: rgb(255, 255, 255);\
                   background-color: rgb(255, 128, 0);", 
            'd' : "background-color: rgb(255, 128, 0);",
            'l' : "background-color: rgb(21, 7, 7);\
                   color: rgb(255, 128, 0);",
        }
        layerName = button.buttonData['formValues'][u'*Selecione camada:']
        styleToClick = styles[layerName.split('_')[-1]]
        button.setStyleSheet(styleToClick)
        self.button = button
        self.menu_functions.startClassification(button, self.reclassificationCheckBox.isChecked())
   
    def validateAddButton(self, formValues):
        buttonName = formValues[u'*Nome do botão:']\
            if formValues[u'*Nome do botão:'] != u'<opções>' else ''
        tabName = formValues[u'*Selecione aba:'] \
            if formValues[u'*Selecione aba:'] != u'<opções>' else ''
        layerName =  formValues[u'*Selecione camada:'] \
            if formValues[u'*Selecione camada:'] != u'<opções>' else ''
        allButtonName = []
        if buttonName and tabName and layerName:
            profile = self.menu_functions.getProfileMenu()
            for tabName in profile:
                for bn in profile[tabName]:
                    allButtonName.append(bn)
            if not buttonName in allButtonName:
                return True
        return False   
    
    def removeButtonLayer(self, formValues, fields):
        tabName = formValues[u'*Selecionar aba:']
        buttonName = formValues[u'*Selecionar bot\xe3o:']
        self.tabWidget.removeButtonLayer({
            'tabName' : tabName,
            'buttonName' : buttonName,
        })
        profile = self.menu_functions.getProfileMenu()
        if buttonName in profile[tabName]:
            del  profile[tabName][buttonName]
        self.addTabSearch(profile)
        self.menu_functions.updateMenuData(self.tabWidget, profile)
    
    def editButtonAttributes(self, formValues, fields):
        buttonOld = fields['buttonOld']
        buttonData = buttonOld.buttonData
        oldName = buttonOld.objectName()
        newName = formValues[u'Nome bot\xe3o : ']
        if newName != oldName:
            buttonData['formValues'][u'*Nome do bot\xe3o:'] = newName
            formatName = '%s_%s'%(newName, buttonOld.text().split('_')[-1])
            buttonOld.setText(formatName)
            buttonOld.setObjectName(newName)
        short = buttonOld.shortcut()
        buttonOld.setShortcut(short)
        for field in formValues:
            if field in buttonData['formValues']:
                buttonData['formValues'][field] = formValues[field]
        tabName = buttonData['formValues'][u'*Selecione aba:']
        profile = self.menu_functions.getProfileMenu()
        del profile[tabName][oldName]
        profile[tabName][newName] = buttonData
        self.addTabSearch(profile)
        self.menu_functions.updateMenuData(self.tabWidget, profile)
                              
    def filterButtonMenuByName(self, text):
        profile = self.menu_functions.getProfileMenu()
        iface = self.iface
        currentLayerType = iface.activeLayer().name()[-1:] if iface.activeLayer() else None
        lyr = iface.activeLayer()
        countSelectedFeatures = iface.activeLayer().selectedFeatureCount() if lyr and lyr.type() == core.QgsMapLayer.VectorLayer else 0
        if profile and text:
            self.tabWidget.showTabSearch()
            buttonsData = self.tabWidget.getAllButtonLayerOnTabByName(u'**Pesquisa**')
            self.hideAllButtonsTab(buttonsData)
            for buttonName in buttonsData:
                data = buttonsData[buttonName].buttonData
                buttonGeomType = data['formValues'][u'*Selecione camada:'][-1:]
                wordKeyField = u'Definir palavras chaves(separar com ";"):'
                words = [x.lower() for x in data['formValues'][wordKeyField].split(';')]
                if (currentLayerType == buttonGeomType) and ((text.lower() in buttonName.lower()) or (text.lower() in words)) :
                    btn = buttonsData[buttonName]
                    btn.show()
                elif ( countSelectedFeatures == 0) and ((text.lower() in buttonName.lower()) or (text.lower() in words)):
                    btn = buttonsData[buttonName]
                    btn.show()
        else:
            self.tabWidget.hideTabSearch()

    def hideAllButtonsTab(self, buttonsData):
        for buttonName in buttonsData:
            btn = buttonsData[buttonName]
            btn.hide()



    
  
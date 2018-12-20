# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic, QtGui, QtWebKit
from qgis import core, gui
import sys, os, json, copy, psycopg2
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from database.postgresql_v2 import Postgresql_v2

from menu.menu_functions import Menu_functions
from managerLoadLayers.loadLayers import LoadLayers
from login.login import Login
from managerNetwork.network import Network
from rules.rules import Rules
from finishActivity import FinishActivity
from activity_widget import Activity_widget
from rotines.rotines_manager import Rotines_Manager
from platform   import system as system_name

#carrega o arquivo da interface .ui
sys.path.append(os.path.dirname(__file__))
GUI, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__),
    'ui',
    'tools_interface.ui'), 
    resource_suffix=''
)

class Tools(QtGui.QDialog, GUI):

    def __init__(self, iface):
        super(Tools, self).__init__()
        self.setupUi(self)
        self.parent = None
        self.iface = iface
        self.data = None
        self.rotinesSpacerItem = None
        self.activitySpacerItem = None
        self.insumosSpacerItem = None
        self.rotinesSpacerItem = None
        self.vLayoutMenuForm = QtGui.QVBoxLayout(self.areaUserForm)
        self.menu_functions = None
        self.rules = None
        self.profile = None
        self.orderMenu = None
        self.profiles = None
        self.postgresql = None
        self.statisticRulesButton.setEnabled(False)
        self.exportProfileToFileButton.setVisible(False)
        self.importProfileFromFileButton.setVisible(False)

    def getDbName(self):
        if self.data:
            return self.data["dados"]["atividade"]["banco_dados"]["nome"]
        return  self.dataBaseCombo.currentText()

    def getWorkspace(self):
        if self.data:
            return self.data["dados"]["atividade"]["unidade_trabalho"]
        return  self.workspaceCombo.currentText()

    def getStyleName(self):
        return self.loadWithCombo.currentText()

    def loadCombo(self, combo, values , firstValue=None):
        combo.clear()
        if firstValue:
            combo.addItem(firstValue)
        combo.addItems(sorted(values))
       
    def loadListWidget(self, listWidget, values):
        self.cleanTabLoadLayers()
        listWidget.addItems(values)

    def cleanTabLoadLayers(self):
        self.allLayersList.clear()
        self.selectionList.clear()
        self.searchMainLineEdit.clear()
        self.searchSelectionLineEdit.clear()
    
    def getRulesSelected(self):
        groupBox = self.listRulesGroupBox
        selections = []
        for idx in range(groupBox.children()[0].count()):
            if groupBox.children()[0].itemAt(idx).widget().isChecked():
                ruleName = groupBox.children()[0].itemAt(idx).widget().text()
                selections.append(ruleName)
        return selections
    
    def loadRulesGroupBox(self, rulesData):
        self.cleanRulesGroupBox()
        rulesGroupBox = self.listRulesGroupBox
        rulesGroupBox.setVisible(False)
        if rulesData:
            dbName = self.dataBaseCombo.currentText()
            tps = []
            for i in rulesData:
                tps.append(rulesData[i]['tipo_estilo'])
            for name in list(set(tps)):
                checkBox = self.createCheckBox(
                    name,
                    rulesGroupBox,
                )
                checkBox.clicked.connect(
                    self.statisticRulesButton.setEnabled
                )
            rulesGroupBox.setVisible(True)

    def cleanRulesGroupBox(self):
        groupBox = self.listRulesGroupBox
        for idx in range(groupBox.children()[0].count()):
            groupBox.children()[0].itemAt(idx).widget().deleteLater()
    
    def loadProfileGroupBox(self):
        self.cleanProfilesGroupBox()
        profileGroupBox = self.listProfilesGroupBox
        profileGroupBox.setVisible(False)
        if self.profiles:
            for name in self.profiles.keys():
                radioButton = self.createRadioButton(
                    name,
                    profileGroupBox,
                )
                radioButton.clicked.connect(
                    self.setMenuProfileSelected
                )
            profileGroupBox.setVisible(True)
    
    def getProfileNameSelected(self):
        groupBox = self.listProfilesGroupBox
        for idx in range(groupBox.children()[0].count()):
            if groupBox.children()[0].itemAt(idx).widget().isChecked():
                return groupBox.children()[0].itemAt(idx).widget().text()
        return False

    def setMenuProfileSelected(self):
        name = self.getProfileNameSelected()
        self.profile = self.profiles[name][0]
        self.orderMenu = self.profiles[name][1]
        self.menu_functions.showMenuClassification()

    def cleanProfilesGroupBox(self):
        groupBox = self.listProfilesGroupBox
        for idx in range(groupBox.children()[0].count()):
            groupBox.children()[0].itemAt(idx).widget().deleteLater()

    def loadInsumos(self):
        self.removeAllInsumos()
        insumos = self.data["dados"]["atividade"]["insumos"]
        for data in insumos:
            self.createInsumosBtn(data)
        insumosSpacerItem = QtGui.QSpacerItem(
            20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding
        )
        self.insumosArea.layout().addItem(insumosSpacerItem)
        self.insumosSpacerItem = insumosSpacerItem

    def removeAllInsumos(self):
        layout = self.insumosArea.layout()
        for idx in range(layout.count()):
            if type(layout.itemAt(idx).widget()) == QtGui.QPushButton:
                layout.itemAt(idx).widget().deleteLater()
        layout.removeItem(self.insumosSpacerItem) if self.insumosSpacerItem else ""

    def createInsumosBtn(self, data):
        bt = QtGui.QPushButton(self)
        bt.setFlat(True)
        bt.setStyleSheet("QPushButton { text-align: left; }")
        bt.setText(data["nome"])
        bt.setObjectName(data["caminho"])
        bt.clicked.connect(
            lambda:self.downloadInsumo(bt)
        )
        self.insumosArea.layout().addWidget(bt)

    def downloadInsumo(self, bt):
        pathOrigin = bt.objectName()
        pathDest = unicode(QtGui.QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino:")).encode('utf-8')
        if pathOrigin and pathDest:
            result =  Network(self).download(pathOrigin, pathDest)
            msg =u'Erro ao salvar arquivo!'
            if result:
                originalName = pathOrigin.split(u"\\")[-1]
                extensao = pathOrigin.split(u".")[-1]
                if extensao in ['tiff', 'ecw']:
                    loadLayers = LoadLayers(self.iface, self.data)
                    r = loadLayers.loadRasterLayer(pathDest, originalName, bt.text())
                    msg = u"Arquivo salvo, mas não foi possível carregar arquivo!" if not(r) else u'Arquivo carregado!'
                else:
                    msg = u"Arquivo salvo. Carregue manualmente o arquivo da pasta!"
            QtGui.QMessageBox.information(
                    self,
                    u"Aviso", 
                    msg
            )

    def createCheckBox(self, name, parent):
        checkBox = QtGui.QCheckBox(name, parent)
        parent.children()[0].addWidget(checkBox)
        return checkBox
                
    def createRadioButton(self, name, parent):
        radioButton = QtGui.QRadioButton(name, parent)
        parent.children()[0].addWidget(radioButton)
        return radioButton
    
    def showEvent(self, e):
        self.postgresql = self.loadPostgresDatabase()
        if self.data:
            self.configModeRemote()
        else:
            self.configModeLocal()
        self.connectSignals()

    def closeEvent(self, e):
        self.disconnectSignals()

    def configModeLocal(self):
        self.loadCombo(
            self.dataBaseCombo,
            self.postgresql.getAliasNamesDb(),
            u'<Opções>',
        )       
        self.toolsTabWidget.setTabEnabled(0, False)
        self.toolsTabWidget.setTabEnabled(1, False)
        self.toolsTabWidget.setTabEnabled(4, False)
        self.toolsTabWidget.setTabEnabled(6, False)
        self.toolsTabWidget.setTabEnabled(5, False)
        self.toolsTabWidget.setTabEnabled(2, False)
        self.toolsTabWidget.setCurrentIndex(3)
        self.dataBaseCombo.setVisible(True)
        self.dataBaseLabel.setVisible(True) 
        
    def configModeRemote(self):
        self.dataBaseCombo.setVisible(False)
        self.dataBaseLabel.setVisible(False)
        self.workspaceCombo.setVisible(False)
        self.workspaceLabel.setVisible(False)
        self.only_geom_ckb.setVisible(False)
        self.loadCombo(
            self.loadWithCombo,
            self.validateStyles()
        )
        self.toolsTabWidget.setTabEnabled(0, True)
        self.toolsTabWidget.setCurrentIndex(6)
        self.toolsTabWidget.setTabEnabled(1, True)
        self.toolsTabWidget.setTabEnabled(2, True)
        self.toolsTabWidget.setTabEnabled(4, False)
        if self.data["dados"][u"perfil"] >= 3:
            self.toolsTabWidget.setTabEnabled(4, True)
        self.loadListWidget(
            self.allLayersList,
            self.validateLayers()
        )
        self.loadActivity()
        self.loadRulesGroupBox(self.validateRules())
        self.profiles = self.getProfilesDataFormated()
        self.loadProfileGroupBox()
        self.loadInsumos()
        self.rotines = Rotines_Manager(self.iface, self)
        self.fme_server_frame.setHidden(True)
        self.load_rotines()
        self.connectSignals()
        self.sendAllButton.click()
        self.sendAllButton.setEnabled(False)
        self.sendSelectionButton.setEnabled(False)
        self.callAllButton.setEnabled(False)
        self.callSelectionButton.setEnabled(False)

    def connectSignals(self):
        if self.data:
            self.loadWithCombo.currentIndexChanged.connect(
                self.updateToolsByStyleCombo
            )
        else:
            self.dataBaseCombo.currentIndexChanged.connect(
                self.updateToolsByDbCombo
            )       
            self.workspaceCombo.currentIndexChanged.connect(
                self.updateToolsByWorkCombo
            )
            self.loadWithCombo.currentIndexChanged.connect(
                self.updateToolsByStyleCombo
            )

    def disconnectSignals(self):
        if self.data:
            try:
                self.loadWithCombo.currentIndexChanged.disconnect(
                    self.updateToolsByStyleCombo
                )
            except:
                pass
        else:
            try:
                self.dataBaseCombo.currentIndexChanged.disconnect(
                    self.updateToolsByDbCombo
                )
            except:
                pass
            try:       
                self.workspaceCombo.currentIndexChanged.disconnect(
                    self.updateToolsByWorkCombo
                )
            except:
                pass
            try:
                self.loadWithCombo.currentIndexChanged.disconnect(
                    self.updateToolsByStyleCombo
                )
            except:
                pass
            
    def updateToolsByStyleCombo(self, idx):
        menu = Menu_functions(self.iface, self.data, self)
        menu.exportDataMenuOnProject() 

    def updateToolsByDbCombo(self, idx):
        menu = Menu_functions(self.iface, self.data, self)
        if idx > 0:
            self.toolsTabWidget.setTabEnabled(0, True)
            self.toolsTabWidget.setTabEnabled(2, True)
            self.toolsTabWidget.setTabEnabled(4, True)
            self.toolsTabWidget.setCurrentIndex(0)
            self.postgresql.connectPsycopg2(self.getDbName())
            self.loadListWidget(
                self.allLayersList,
                self.postgresql.dbJson['listOfLayers']  
            )
            self.loadCombo(
                self.loadWithCombo,
                self.postgresql.getStylesItems()
            )
            self.loadCombo(
                self.workspaceCombo,
                self.postgresql.getWorkspaceItems(),
                u'Todas as unidades'
            )
            self.profiles = self.getProfilesDataFormated()
            self.loadProfileGroupBox()
            menu.exportDataMenuOnProject()
            self.rules = Rules(self.iface)
            rulesData = self.postgresql.getRulesData()
            self.rules.createRules(rulesData)
            self.loadRulesGroupBox(rulesData)
        else:
            self.toolsTabWidget.setTabEnabled(0, False)
            self.toolsTabWidget.setTabEnabled(2, False)
            self.toolsTabWidget.setTabEnabled(5, False)
            self.listRulesGroupBox.setVisible(False)
            self.toolsTabWidget.setTabEnabled(4, False)
            self.listProfilesGroupBox.setVisible(False)
            self.toolsTabWidget.setCurrentIndex(3)
            self.loadCombo(self.loadWithCombo, [])
            self.loadCombo(self.workspaceCombo, [])
            self.cleanProfilesGroupBox()
            self.rulesWebView.setHtml('')
            self.cleanRulesGroupBox()
            menu.exportDataMenuOnProject()

    def getProfilesDataFormated(self):
        profilesData = self.postgresql.getProfilesData()
        profiles = {}
        if self.data:
            for profile in self.data["dados"]["atividade"]["menus"]:
                for i in profilesData:
                    if profile == profilesData[i][u"nome_do_perfil"]:
                        profiles[profilesData[i]['nome_do_perfil']] = [
                            profilesData[i]['perfil'], 
                            profilesData[i]['orderMenu']
                        ]
        else:
            for i in profilesData:
                profiles[profilesData[i]['nome_do_perfil']] = [
                    profilesData[i]['perfil'], 
                    profilesData[i]['orderMenu']
                ]
        return profiles
        
    def updateToolsByWorkCombo(self, idx):
        menu = Menu_functions(self.iface,  self.data, self)
        if idx > 0:
            self.toolsTabWidget.setTabEnabled(1, True)
            menu.exportDataMenuOnProject()
        else:
            self.toolsTabWidget.setTabEnabled(1, False)
            menu.exportDataMenuOnProject()

    def showAllRotineWidget(self):
        layout = self.rotinesArea.layout()
        for idx in range(layout.count()):
            if type(layout.itemAt(idx)) == QtGui.QWidgetItem:
                layout.itemAt(idx).widget().setVisible(True)

    @QtCore.pyqtSlot(str)
    def on_searchRotinesLineEdit_textEdited(self, text):
        self.showAllRotineWidget()
        if text:
            layout = self.rotinesArea.layout()
            for idx in range(layout.count()):
                if type(layout.itemAt(idx)) == QtGui.QWidgetItem:
                    rotine_descr = layout.itemAt(idx).widget().text()
                    if not(text.lower() in rotine_descr.lower()):
                        layout.itemAt(idx).widget().setVisible(False)

    def remove_all_rotines(self):
        layout = self.rotinesArea.layout()
        for idx in range(layout.count()):
            if type(layout.itemAt(idx).widget()) == QtGui.QPushButton:
                layout.itemAt(idx).widget().deleteLater()
        layout.removeItem(self.rotinesSpacerItem) if self.rotinesSpacerItem else ""

    def load_rotines(self):
        rotines_fme = self.rotines.getRotinesFme()
        rotines_local = self.data["dados"]["atividade"]["rotinas"] if self.data else False
        if rotines_fme:
            for rotine in rotines_fme['data']:
                radio_btn = self.createRadioButton(
                    rotine['workspace_description'], 
                    self.rotinesArea
                )
                rotine.update({'type_rotine' : 'fme'})
                radio_btn.setObjectName(json.dumps(rotine))
        if rotines_local:
            descript = {
                u"notSimpleGeometry" : u"Identifica geometrias não simples.",
                u"outOfBoundsAngles" : u"Identifica ângulos fora da tolerância.",
                u"invalidGeometry" : u"Identifica geometrias inválidas."
            }
            for rotine_name in rotines_local:
                radio_btn = self.createRadioButton(
                    descript[rotine_name], 
                    self.rotinesArea
                )
                radio_btn.setObjectName(json.dumps({
                    rotine_name : rotines_local[rotine_name],
                    'type_rotine' : 'local'
                }))
        insumosSpacerItem = QtGui.QSpacerItem(
            20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding
        )
        self.rotinesArea.layout().addItem(insumosSpacerItem)
        self.rotinesSpacerItem = insumosSpacerItem
    
    @QtCore.pyqtSlot(bool)
    def on_reloadRotinesButton_clicked(self, b):
        self.remove_all_rotines()
        self.rotines = Rotines_Manager(self.iface, self)
        self.load_rotines()
    
    def getSelectedRotine(self):
        groupBox = self.rotinesArea
        for idx in range(groupBox.children()[0].count()):
            if groupBox.children()[0].itemAt(idx).widget().isChecked():
                return json.loads(groupBox.children()[0].itemAt(idx).widget().objectName())
        
    @QtCore.pyqtSlot(bool)
    def on_runRotineButton_clicked(self, b):
        rotine_data = self.getSelectedRotine()
        if rotine_data:
            self.rotines.startRotine(rotine_data)
       
    def moveAllItemsOfList(self, listOrigin, listDestination):
        itemsFromOrigin = [
            listOrigin.item(x) for x in range(listOrigin.count())
        ]
        itemsFromDestination = [ 
            listDestination.item(x) for x in range(listDestination.count())
        ]
        for item in itemsFromOrigin:
            if not item.text() in [i.text() for i in itemsFromDestination]:
                listDestination.addItem(item.text())
        listDestination.sortItems()
        for item in itemsFromOrigin:
            listOrigin.takeItem(listOrigin.row(item))

    def moveSelectedItemsOfList(self, listOrigin, listDestination):
        itemsFromOrigin = [
                item for item in listOrigin.selectedItems()
        ]
        itemsFromDestination = [ 
            listDestination.item(x) for x in range(listDestination.count())
        ]
        for item in itemsFromOrigin:
            if not item.text() in [i.text() for i in itemsFromDestination]:
                listDestination.addItem(item.text())
        listDestination.sortItems()
        for item in itemsFromOrigin:
            listOrigin.takeItem(listOrigin.row(item))

    def searchLayersList(self, widgetList, text):
        itemsFromList = [
            widgetList.item(x) for x in range(widgetList.count())
        ]
        for item in itemsFromList:
            if not text in item.text():
                item.setHidden(True)
            else:
                item.setHidden(False)

    @QtCore.pyqtSlot(bool)
    def on_sendAllButton_clicked(self, b):
        origin = self.allLayersList
        destination = self.selectionList
        self.moveAllItemsOfList(origin, destination)
    
    @QtCore.pyqtSlot(bool)
    def on_sendSelectionButton_clicked(self, b):
        origin = self.allLayersList
        destination = self.selectionList
        self.moveSelectedItemsOfList(origin, destination)
 
    @QtCore.pyqtSlot(bool)
    def on_callAllButton_clicked(self, b):
        origin = self.selectionList
        destination = self.allLayersList
        self.moveAllItemsOfList(origin, destination) 

    @QtCore.pyqtSlot(bool)
    def on_callSelectionButton_clicked(self, b):
        origin = self.selectionList
        destination = self.allLayersList    
        self.moveSelectedItemsOfList(origin, destination)

    def getLayersSelected(self):
        itemsSelected = [
            self.selectionList.item(x).text()
            for x in range(self.selectionList.count())
        ]
        return itemsSelected

    def loadPostgresDatabase(self):
        postgresql = Postgresql_v2(self.iface)
        if self.data:
            postgresql.connectPsycopg2WithLoginData(self.data)
        else:
            try:
                postgresql.connectPsycopg2(self.getDbName()) if self.getDbName() else ""
            except psycopg2.OperationalError:
                QtGui.QMessageBox.critical(
                    self,
                    u"Erro", 
                    u"Usuário ou senha incorretos!"
                )
        return postgresql

    @QtCore.pyqtSlot(bool)
    def on_loadButton_clicked(self, b):
        itemsSelected = self.getLayersSelected()
        if itemsSelected:
            self.loadLayersProgressBar.setMaximum(len(itemsSelected))
            loadLayers = LoadLayers(self.iface, self.data)
            loadLayers.rules = self.rules
            loadLayers.updateProgressBar.connect(
                self.updateProgressBar
            )
            loadLayers.setFilters(self.postgresql.getFilterData())
            loadLayers.loadAllLayersSelected({
                'activeProgressBar' : True,
                'layersSelected' : itemsSelected,
                'layersSelectedFormated' : self.formatSelectedItems(
                    itemsSelected
                ),
                'dbAlias' : self.getDbName(), 
                'workspace' : self.getWorkspace(),
                'styleName' : self.getStyleName(),
                'selectedRulesType' : self.getRulesSelected(),
                'dbJson' : self.postgresql.dbJson,
                'only_geom' : self.only_geom_ckb.isChecked(),
            })
            self.resetProgressbar(itemsSelected)
    
    def formatSelectedItems(self, itemsSelected):
        selectedItemsFormated = {}
        groupGeom = {'a' : 'AREA', 
                     'c' : 'PONTO',
                     'p' : 'PONTO', 
                     'd' : 'LINHA',
                     'l' : 'LINHA',}
        for item in itemsSelected:
            group = groupGeom[item.split('_')[-1]]
            if not(group in selectedItemsFormated):
                selectedItemsFormated[group] = {}
            catLayer = item.split('_')[0]
            if not(catLayer in selectedItemsFormated[group]):
                selectedItemsFormated[group][catLayer] = []
            selectedItemsFormated[group][catLayer].append(item)
        return selectedItemsFormated  

    def resetProgressbar(self, itemsSelected):
        self.loadLayersProgressBar.setValue(len(itemsSelected))
        self.loadLayersProgressBar.setValue(0)
        self.callAllButton.click()    
                   
    def updateProgressBar(self):
        self.loadLayersProgressBar.setValue(self.loadLayersProgressBar.value() + 1)

    @QtCore.pyqtSlot(str)
    def on_searchMainLineEdit_textEdited(self, text):
        self.searchLayersList(self.allLayersList, text)
        
    @QtCore.pyqtSlot(str)        
    def on_searchSelectionLineEdit_textEdited(self, text):
        self.searchLayersList(self.selectionList, text)

    @QtCore.pyqtSlot(bool)
    def on_statisticRulesButton_clicked(self, b):
        if self.data:
            db_name = self.getWorkspace()
        else:
            db_name = self.getDbName()+"-"+self.getWorkspace()
        if db_name:
            self.rulesWebView.setHtml('')
            self.rulesProgressBar.setValue(50)
            statisticHtml = self.rules.getStatisticRules(
                self.getRulesSelected(),
                db_name
            )
            if statisticHtml:
                self.rulesWebView.setHtml(statisticHtml)
            self.rulesProgressBar.setValue(100) 
            self.rulesProgressBar.setValue(0) 
   
    @QtCore.pyqtSlot(bool)
    def on_openMenuButton_clicked(self):
        self.menu_functions.closeMenuClassification()
        self.menu_functions.showMenuClassification()

    ''' @QtCore.pyqtSlot(bool)
    def on_exportProfileToFileButton_clicked(self):
        self.menu_functions.showFormSaveProfileOnFile()

    @QtCore.pyqtSlot(bool)
    def on_importProfileFromFileButton_clicked(self):
        self.menu_functions.showFormLoadProfileOnFile() '''

    @QtCore.pyqtSlot(bool)
    def on_addTabButton_clicked(self):
        self.menu_functions.showFormAddTabMenu()
            
    @QtCore.pyqtSlot(bool)
    def on_removeTabButton_clicked(self):
        self.menu_functions.showFormDelTabMenu()
        
    @QtCore.pyqtSlot(bool)  
    def on_addButtonLayerButton_clicked(self):
        self.menu_functions.showFormAddButtonMenu()
           
    @QtCore.pyqtSlot(bool)
    def on_removeButtonLayerButton_clicked(self):
        self.menu_functions.showFormDelButtonMenu()
        
    @QtCore.pyqtSlot(bool) 
    def on_exportProfileToDbButton_clicked(self):
        self.menu_functions.showFormSaveProfileOnDb()

    @QtCore.pyqtSlot(bool) 
    def on_editTabButton_clicked(self):
        self.menu_functions.showEditTabMenu()

    @QtCore.pyqtSlot(bool) 
    def on_editButtonButton_clicked(self):
        self.menu_functions.showEditAttributesButton()
    
    @QtCore.pyqtSlot(bool)
    def on_finishActivityButton_clicked(self):
        if self.validate_finish_active():
            finish_dlg = FinishActivity(self.data)
            finish_dlg.finish.connect(self.parent.finishActivity)
            finish_dlg.exec_()

    def validate_finish_active(self):
        for lyr in core.QgsMapLayerRegistry.instance().mapLayers().values():
            test = (
                lyr.type() == core.QgsMapLayer.VectorLayer
                and
                lyr.editBuffer() and lyr.isModified()
            )
            if test:
                QtGui.QMessageBox.critical(
                    self,
                    u"Erro", 
                    u'<p style="color:red;">Salve todas as camadas antes de finalizar o projeto!</p>'
                )
                return False
        return True
    
    def removeAllActivity(self):
        activityArea = self.activityArea.layout()
        for idx in range(activityArea.count()):
            if type(activityArea.itemAt(idx)) == QtGui.QWidgetItem:
                activityArea.itemAt(idx).widget().deleteLater()
        activityArea.layout().removeItem(self.activitySpacerItem) if self.activitySpacerItem else ""
            

    def loadActivity(self):
        self.removeAllActivity()
        if self.data:
            description = self.data["dados"]["atividade"]["nome"]
            values_cbx = (
                self.data["dados"]["atividade"]["requisitos"]
                if "requisitos" in self.data["dados"]["atividade"] else []
            )
            self.finishActivityButton.setEnabled(False) if len(values_cbx) > 0 else ""
            self.activity = Activity_widget(description, values_cbx, self)
            self.activity.enable_finish.connect(lambda:self.finishActivityButton.setEnabled(True))
            self.activity.disable_finish.connect(lambda:self.finishActivityButton.setEnabled(False))
            self.activityArea.layout().addWidget(self.activity)
        else:
            label = QtGui.QLabel(self)
            label.setText(u"<h1>Não há atividades em execução!</h1>")
            self.activityArea.layout().addWidget(label)
        activitySpacerItem = QtGui.QSpacerItem(
            20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding
        )
        self.activityArea.layout().addItem(activitySpacerItem)
        self.activitySpacerItem = activitySpacerItem

    def validateFiltersOptions(self):
        ok = []
        workspace = self.getWorkspace()
        return []
   
    def validateStyles(self):
        styles_name = self.data["dados"]["atividade"]["estilos"]
        return self.postgresql.getStylesItems(styles_name)
    
    def validateRules(self):
        ok = {}
        rulesData = self.postgresql.getRulesData()
        for rule in self.data["dados"]["atividade"]["regras"]:
            for i in rulesData:
                if rule == rulesData[i][u"tipo_estilo"]:
                        ok[i] = rulesData[i]
        self.rules = Rules(self.iface)
        self.rules.createRules(ok)
        return ok  
 
    def validateLayers(self):
        return self.postgresql.dbJson['listOfLayers']
   
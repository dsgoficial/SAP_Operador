#! -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from menu_button import Menu_button

class Menu_tabWidget(QtGui.QTabWidget):
    def __init__(self, parent=None):
        super(Menu_tabWidget, self).__init__(parent)
        self.setTabPosition(QtGui.QTabWidget.West)
        self.setElideMode(QtCore.Qt.ElideNone)
        self.setStyleSheet("QTabBar::tab::disabled {width: 0; heigth: 0; margin: 0; padding: 0; border: none;}")
        
    def getShortCut(self):
        return {
            0 : QtCore.Qt.Key_1,
            1 : QtCore.Qt.Key_2,
            2 : QtCore.Qt.Key_3,
            3 : QtCore.Qt.Key_4,
            4 : QtCore.Qt.Key_5,
            5 : QtCore.Qt.Key_6,
            6 : QtCore.Qt.Key_7,
            7 : QtCore.Qt.Key_8,
            8 : QtCore.Qt.Key_9
        }

    def addTabs(self, tabName):
        tab = QtGui.QWidget()
        layoutTab = QtGui.QVBoxLayout(tab)
        layoutTab.setObjectName(u'area')
        scrollArea = QtGui.QScrollArea(tab)
        scrollArea.setWidgetResizable(True)
        scrollAreaWidgetContents = QtGui.QWidget()
        scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 328, 386))
        scrollAreaWidgetContents.setObjectName(u'scroll')
        layoutButton = QtGui.QVBoxLayout(scrollAreaWidgetContents)
        layoutButton.setObjectName(u'layout')
        scrollArea.setWidget(scrollAreaWidgetContents)
        layoutTab.addWidget(scrollArea)
        if tabName == u'**Pesquisa**':
            if u'**Pesquisa**' in self.getAllNamesTabs():
                self.cleanTab(u'**Pesquisa**')
            else:
                self.insertTab(0, tab, tabName)
                self.setTabEnabled(0, False)
        else:
            self.insertTab(1, tab, tabName)
        self.setCurrentIndex(1)
    
    def addButtonLayer(self, data):
        nameButton = data[u'formValues'][u'*Nome do botão:']
        tabName = data[u'formValues'][u'*Selecione aba:']
        scrollAndLayoutTab = self.getScrollAndLayoutTabByName(tabName)
        scrollTab = scrollAndLayoutTab['scroll']
        layoutTab = scrollAndLayoutTab['layout']
        count = layoutTab.count()
        button = Menu_button({
            u'parent' : scrollTab,
            u'buttonData' : data,
        })
        button.createButtonLayer()
        layoutTab.addWidget(button)
        if count >=0 and count <= 8:
            button.setText(button.text()+'_[%i]'%(count+1))
            button.setShortcut(self.getShortCut()[count])
        return button

    def getAllNamesTabs(self):
        tabs = {}
        for idx in range(self.count()):
            tabs[self.tabText(idx)] = idx
        return tabs

    def cleanAllTabWidget(self):
        for tabName in self.getAllNamesTabs():
            self.removeTabByName(tabName)

    def cleanTab(self, tabName):
        buttons = self.getAllButtonLayerOnTabByName(tabName)
        for buttonName in buttons:
            buttons[buttonName].deleteLater()
            
    def removeTabByName(self, tabName):
        for idx in range(self.count()):
            if tabName == self.tabText(idx):
                self.removeTab(idx)

    def getScrollAndLayoutTabByName(self, tabName):
        allTabs = self.getAllNamesTabs()
        scroll = self.widget(allTabs[tabName])\
                     .findChildren(QtGui.QScrollArea)[0].children()[0].children()[0]
        layout = scroll.children()[0]
        data = {
            'scroll' : scroll,
            'layout' : layout,
        }
        return data
       
    def getAllButtonLayerOnTabByName(self, tabName):
        buttons = {}
        data = self.getScrollAndLayoutTabByName(tabName)
        for idx in range(data['layout'].count()):
            name = data['layout'].itemAt(idx).widget().objectName()
            widget = data['layout'].itemAt(idx).widget()
            buttons[name] = widget
        return buttons

    def getButtonLayerWidget(self, data):
        tabName = data['tabName']
        buttonName = data['buttonName']
        buttons = self.getAllButtonLayerOnTabByName(tabName)
        return buttons[buttonName]

    def removeButtonLayer(self, data):
        buttonWidget = self.getButtonLayerWidget(data)
        buttonWidget.deleteLater()

    def reloadStandardStylesButtons(self):
        for tabName in  self.getAllNamesTabs():
            buttons = self.getAllButtonLayerOnTabByName(tabName)
            for buttonName in buttons:
                button = buttons[buttonName]
                button.setStyleSheet(button.styleDefault)

    def getOrderMenu(self):
        orderMenu = {
            "orderTab" : [],
            "orderButton" : {},
        }
        for idx in range(self.count()):
            tabName = self.tabText(idx)
            if not(tabName in [u'**Pesquisa**']):
                orderMenu["orderTab"].append(tabName)
                orderMenu["orderButton"][tabName] = []
                data = self.getScrollAndLayoutTabByName(tabName)
                for idx in range(data['layout'].count()):
                    buttonName = data['layout'].itemAt(idx).widget().objectName()
                    orderMenu["orderButton"][tabName].append(buttonName)
        return orderMenu             

    def showTabSearch(self):
        self.setTabEnabled(0, True)
        self.setCurrentIndex(0)

    def hideTabSearch(self):
        self.setTabEnabled(0, False)
        if self.isTabEnabled(1):
            self.setCurrentIndex(1)
        else:
            self.setCurrentIndex(1) 
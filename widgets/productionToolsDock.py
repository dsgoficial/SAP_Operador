from Ferramentas_Producao.interfaces.IProductionToolsDock import IProductionToolsDock
from Ferramentas_Producao.config  import Config

import os, sys, copy
from PyQt5 import QtCore, uic, QtWidgets, QtGui

class ProductionToolsDock(QtWidgets.QDockWidget, IProductionToolsDock):

    def __init__(self):
        super(ProductionToolsDock, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.setWindowTitle(Config.NAME)
        self.controller = None
        self.shortcutTE.setReadOnly(True)   
        self.tabWidget.removeTab( 3 )
        self.tabWidget.currentChanged.connect(self.handleTabChanged)  
        self.widgets = []

    def handleTabChanged(self, idx):
        if idx == self.getTabIndexByName('errors'):  
            self.setBadgeTabErrorsEnabled(False) 
    
    def getTabIndexByName(self, tabName):
        return self.tabWidget.indexOf(self.tabWidget.findChild(QtWidgets.QWidget, tabName))

    def isCurrentTab(self, tabName):
        tabIdx = self.tabWidget.indexOf(self.tabWidget.findChild(QtWidgets.QWidget, tabName))
        return tabIdx == self.tabWidget.currentIndex()

    def setBadgeTabErrorsEnabled(self, enable):
        if enable and self.isCurrentTab('errors'):
            return
        badgeIconPath =  os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'icons',
            'badgeError.svg'
        )
        iconPath = badgeIconPath if enable else ''
        idx = self.tabWidget.indexOf(self.tabWidget.findChild(QtWidgets.QWidget, 'errors'))
        self.tabWidget.setTabIcon( idx, QtGui.QIcon( iconPath ) )

    def setController(self, controller):
        self.controller = controller

    def getController(self):
        return self.controller

    def removeTab(self, index):
        self.tabWidget.removeTab(index)

    def removeAllWidgets(self):
        for layout in [self.lineageArea.layout(), self.mainArea.layout()]:
            if not layout:
                continue
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is None:
                    continue
                widget.deleteLater()

    def closeEvent(self, e):
        self.getController().closedDock()
    
    def getItemIcon(self):
        return QtGui.QIcon(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                '..',
                'icons',
                'config.png'
            )
        )
        

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 
            '..',
            'uis',
            'productionToolsDock.ui'
        )

    def addLine(self):
        lineA = QtWidgets.QFrame()
        lineA.setFrameShape(QtWidgets.QFrame.HLine)
        lineA.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.mainArea.layout().insertWidget(0, lineA)

    def addActivityWidget(self, name, widget):
        self.widgets.append({
            'name': name,
            'widget': widget
        })
        self.mainArea.layout().insertWidget(0, widget)

    def getActivityWidget(self, name):
        found = next(filter(lambda item: item['name'] == name, self.widgets), None)
        if found:
            return found['widget']
        return None

    def setShortcutDescription(self, description):
        self.shortcutTE.setHtml(description)

    def addPomodoro(self, pomodoro):
        self.pomodoroArea.layout().addWidget(pomodoro)

    def addLineageLabel(self, lineage):
        text = "Etapa : {0}\nSituação: {5}\nData inicio : {1}\nData fim : {2}\nNome : {3} {4}".format(
            lineage['etapa'] if lineage['etapa'] else '-', 
            lineage['data_inicio'] if lineage['data_inicio'] else '-', 
            lineage['data_fim'] if lineage['data_fim'] else '-', 
            lineage['posto_grad'] if lineage['posto_grad'] else '', 
            lineage['nome_guerra'] if lineage['nome_guerra'] else '-', 
            lineage['situacao'] if lineage['situacao'] else '-', 
        )
        label = QtWidgets.QLabel(text)
        label.setStyleSheet('QLabel { background-color: white }')
        self.lineageArea.layout().insertWidget(0, label)

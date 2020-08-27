from Ferramentas_Producao.interfaces.IProductionToolsDock import IProductionToolsDock
from Ferramentas_Producao.config  import Config

import os, sys, copy
from PyQt5 import QtCore, uic, QtWidgets, QtGui

class ProductionToolsDock(QtWidgets.QDockWidget, IProductionToolsDock):

    def __init__(self):
        super(ProductionToolsDock, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.setWindowTitle(Config.NAME)
        self.tabWidget.setTabIcon(0, self.getTabIcon())
        self.tabWidget.setTabIcon(1, self.getTabIcon())
        self.treeWidgetActivity = QtWidgets.QTreeWidget()
        self.treeWidgetActivity.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.treeWidgetActivity.setColumnCount(1)
        self.treeWidgetActivity.header().hide()
        self.connectQtreeWidgetSignals(self.treeWidgetActivity)
        self.mainArea.layout().addWidget(self.treeWidgetActivity)

    def removeAllWidgets(self):
        self.treeWidgetActivity.clear()
        if not self.lineageArea.layout():
            return
        while self.lineageArea.layout().count():
            item = self.lineageArea.layout().takeAt(0)
            widget = item.widget()
            if widget is None:
                continue
            widget.deleteLater()

    def getTabIcon(self):
        return QtGui.QIcon(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                '..',
                'icons',
                'DSG.svg'
            )
        )
    
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

    def connectQtreeWidgetSignals(self, treeWidget):
        """ treeWidget.itemExpanded.connect(
            self.handleItemExpanded
        ) """
        treeWidget.itemCollapsed.connect(
            self.handleItemCollapsed
        )

    def disconnectQtreeWidgetSignals(self, treeWidget):
        """ treeWidget.itemExpanded.disconnect(
            self.handleItemExpanded
        ) """
        treeWidget.itemCollapsed.disconnect(
            self.handleItemCollapsed
        )

    def handleItemCollapsed(self, item):
        item.setExpanded(True)
        """ treeWidget = self.sender()
        treeWidget.collapseAll()
        self.disconnectQtreeWidgetSignals(treeWidget)
        item.setExpanded(True)
        self.connectQtreeWidgetSignals(treeWidget) """

    def handleItemExpanded(self, item):
        treeWidget = self.sender()
        treeWidget.collapseAll()
        self.disconnectQtreeWidgetSignals(treeWidget)
        item.setExpanded(True)
        self.connectQtreeWidgetSignals(treeWidget)

    def addActivityWidget(self, name, widget):
        topLevelItem = QtWidgets.QTreeWidgetItem([name])
        topLevelItem.setIcon(0, self.getItemIcon())
        childItem = QtWidgets.QTreeWidgetItem()
        topLevelItem.addChild(childItem)
        self.treeWidgetActivity.addTopLevelItem(topLevelItem)
        self.treeWidgetActivity.setItemWidget(childItem, 0, widget)
        topLevelItem.setExpanded(True)

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
        self.lineageArea.layout().addWidget(label)

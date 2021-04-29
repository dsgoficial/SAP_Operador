# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from Ferramentas_Producao.widgets.managementWidget  import ManagementWidget

class ErrorWidget(ManagementWidget):
    
    def __init__(self, controller):
        super(ErrorWidget, self).__init__(controller=controller)
        self.tableWidget.cellDoubleClicked.connect(self.zoomToFeature)
        self.clearButton.setIcon(
            QtGui.QIcon(
                self.getClearIconPath()
            )
        )
        self.clearButton.setIconSize(QtCore.QSize(25, 25))

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'errorWidget.ui'
        )

    def getClearIconPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'icons',
            'clear.jpeg'
        )

    def addRow(self, errorId, layerName, errorMessage):
        idx = self.getRowIndex(errorId)
        if idx < 0:
            idx = self.tableWidget.rowCount()
            self.tableWidget.insertRow(idx)
        self.tableWidget.setItem(idx, 0, self.createNotEditableItem(errorId))
        self.tableWidget.setItem(idx, 1, self.createNotEditableItem(layerName))
        self.tableWidget.setItem(idx, 2, self.createNotEditableItem(errorMessage))

    def addRows(self, data):
        self.clearAllItems()
        for item in data:
            self.addRow(
                item['id'],
                item['layerName'],
                item['message']
            )
        self.adjustColumns()

    def getRowIndex(self, errorId):
        for idx in range(self.tableWidget.rowCount()):
            if not (
                    errorId == self.tableWidget.model().index(idx, 0).data()
                ):
                continue
            return idx
        return -1

    def zoomToFeature(self, row, column):
        self.getController().zoomToFeature(
            self.tableWidget.model().index(row, 0).data(),
            self.tableWidget.model().index(row, 1).data().split('.')[0],
            self.tableWidget.model().index(row, 1).data().split('.')[1]
        )

    @QtCore.pyqtSlot(bool)
    def on_clearButton_clicked(self):
        self.clearAllItems()
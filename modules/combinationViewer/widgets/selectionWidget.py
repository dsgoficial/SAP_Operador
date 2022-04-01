import os, sys, copy, json
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory
from .tableFunctions import TableFunctions

class SelectionWidget(QtWidgets.QWidget, TableFunctions):

    selectionChange = QtCore.pyqtSignal()

    def __init__(self, 
            controller, 
            parent=None,
            messageFactory=UtilsFactory().createMessageFactory()
        ):
        super(SelectionWidget, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.controller = controller
        self.messageFactory = messageFactory
        self.sendTw.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.selectionTw.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'selectionWidget.ui'
        )

    def setup(self, setup):
        self.sendTw.setSortingEnabled(True)
        self.selectionTw.setSortingEnabled(True)
        self.titleLb.setText(setup['title'])
        self.addSendColumns(setup['send']['columns'])
        self.addSelectionColumns(setup['selection']['columns'])
        self.setup = setup

    def addSendColumns(self, columns):
        self.addColumns(self.sendTw, columns)

    def addSendRows(self, rows):
        self.addRows(self.sendTw, rows)

    def clearSendRows(self):
        self.clearAllItems(self.sendTw)
        self.selectionChange.emit()

    def setSendColumnHidden(self, col, visible):
        self.sendTw.setColumnHidden(col, visible)

    def addSelectionColumns(self, columns):
        self.addColumns(self.selectionTw, columns)

    def addSelectionRows(self, rows):
        self.addRows(self.selectionTw, rows)

    def clearSelectionRows(self):
        self.clearAllItems(self.selectionTw)
        self.selectionChange.emit()

    def setSelectionColumnHidden(self, col, visible):
        self.selectionTw.setColumnHidden(col, visible)

    @QtCore.pyqtSlot(str)
    def on_sendFilterLe_textEdited(self, text):
        self.searchRows(self.sendTw, text)

    @QtCore.pyqtSlot(str)
    def on_selectionFilterLe_textEdited(self, text):
        self.searchRows(self.selectionTw, text)

    @QtCore.pyqtSlot(bool)
    def on_selectAllBtn_clicked(self):
        rows = self.popAllRows(self.sendTw)
        self.addSelectionRows(rows)
        self.selectionChange.emit()

    @QtCore.pyqtSlot(bool)
    def on_selectBtn_clicked(self):
        rows = self.popSelectedRows(self.sendTw)
        self.addSelectionRows(rows)
        self.selectionChange.emit()

    @QtCore.pyqtSlot(bool)
    def on_unselectAllBtn_clicked(self):
        rows = self.popAllRows(self.selectionTw)
        self.addSendRows(rows)
        self.selectionChange.emit()

    @QtCore.pyqtSlot(bool)
    def on_unselectBtn_clicked(self):
        rows = self.popSelectedRows(self.selectionTw)
        self.addSendRows(rows)
        self.selectionChange.emit()

    def popSelectedRows(self, tableWidget):
        rows = []
        while tableWidget.selectionModel().selectedRows():
            m = tableWidget.selectionModel().selectedRows()[0]
            rowIdx = m.row()
            row = []
            for colIdx in range(tableWidget.columnCount()):
                item = tableWidget.item(rowIdx, colIdx)
                row.append(item.text())
            tableWidget.removeRow(rowIdx)
            rows.append(row)
        return rows

    def popAllRows(self, tableWidget):
        rows = []
        while range(tableWidget.rowCount()):
            rowIdx = range(tableWidget.rowCount())[0]
            row = []
            for colIdx in range(tableWidget.columnCount()):
                item = tableWidget.item(rowIdx, colIdx)
                row.append(item.text())
            tableWidget.removeRow(rowIdx)
            rows.append(row)
        return rows

    def getSelectedData(self):
        tableWidget = self.selectionTw
        rows = []
        for rowIdx in range(tableWidget.rowCount()):
            row = []
            for colIdx in range(tableWidget.columnCount()):
                item = tableWidget.item(rowIdx, colIdx)
                row.append(item.text())
            rows.append(row)
        return rows

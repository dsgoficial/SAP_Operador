import os, sys, copy
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from .qTableWidgetIntegerItem import QTableWidgetIntegerItem

class TableFunctions(QtCore.QObject):

    def countTableRows(self, tableWidget):
        return tableWidget.rowCount()

    def validateValue(self, value):
        if value is None:
            return ''
        return str(value)

    def createNotEditableItem(self, value):
        itemValue = self.validateValue(value)
        try:
            item = QTableWidgetIntegerItem(itemValue)
        except:
            item = QtWidgets.QTableWidgetItem(itemValue)
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        return item

    def createEditableItem(self, value):
        item = QtWidgets.QTableWidgetItem(self.validateValue(value))
        return item

    def searchRows(self, tableWidget, text):
        columns = range(tableWidget.columnCount())
        for idx in range(tableWidget.rowCount()):
            if text and not self.hasTextOnRow(tableWidget, idx, columns, text):
                tableWidget.setRowHidden(idx, True)
            else:
                tableWidget.setRowHidden(idx, False)

    def hasTextOnRow(self, tableWidget, rowIdx, columns, text):
        for colIdx in columns:
            cellText = tableWidget.model().index(rowIdx, colIdx).data()
            if cellText and text.lower() in cellText.lower():
                return True
        return False

    def clearAllItems(self, tableWidget):
        tableWidget.setRowCount(0)

    def adjustColumns(self, tableWidget):
        tableWidget.resizeColumnsToContents()

    def adjustRows(self, tableWidget):
        tableWidget.resizeRowsToContents()

    def hideTableColumns(self, b, tableWidget, columns):
        for column in columns:
            tableWidget.setColumnHidden(column, b)
        self.adjustColumns(tableWidget)
        self.adjustRows(tableWidget)    

    def setupTableWidget(self, tableWidget, hideColumns):
        self.hideTableColumns(True, tableWidget, hideColumns)
        tableWidget.horizontalHeader().sortIndicatorOrder()
        tableWidget.setSortingEnabled(True)
        self.adjustColumns(tableWidget)

    def getRowIndex(self, tableWidget, primarykey, column=0):
        for idx in range(tableWidget.rowCount()):
            if not (
                primarykey == tableWidget.model().index(idx, column).data()
            ):
                continue
            return idx
        return -1

    def setColorToRow(self, table, rowIndex, color):
        for j in range(table.columnCount()):
            try:
                self.setColorToCell(table, rowIndex, j, color)
            except:
                pass

    def setColorToCell(self, table, rowIndex, column, color):
        table.item(rowIndex, column).setBackground(color)

    def addColumns(self, tableWidget, columns):
        tableWidget.setColumnCount(len(columns))
        tableWidget.setHorizontalHeaderLabels(columns)
        self.adjustColumns(tableWidget)
        self.adjustRows(tableWidget)

    def addRows(
            self,
            tableWidget, 
            rows
        ):
        for idx, row in enumerate(rows):
            self.addRow(tableWidget, idx, row)
        self.adjustColumns(tableWidget)
        self.adjustRows(tableWidget)

    def addRow(
            self,
            tableWidget, 
            rowIdx,
            row
        ):
        tableWidget.insertRow(rowIdx)
        for colIdx, fieldValue in enumerate(row):
            item = self.createNotEditableItem(fieldValue)
            tableWidget.setItem(rowIdx, colIdx, item)

    
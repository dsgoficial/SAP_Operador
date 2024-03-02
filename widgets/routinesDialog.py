import os, sys, copy, json
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from SAP_Operador.modules.utils.factories.utilsFactory import UtilsFactory

class RoutinesDialog(QtWidgets.QDialog):
    
    def __init__(self, 
            controller, 
            parent=None,
            messageFactory=None,
        ):
        super(RoutinesDialog, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.tableWidget.horizontalHeader().sortIndicatorOrder()
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.setColumnHidden(0, True)
        self.currentRoutineData = {}
        self.controller = controller
        self.messageFactory = UtilsFactory().createMessageFactory() if messageFactory is None else messageFactory
    
    def getController(self, controller):
        self.controller = controller
    
    def setController(self):
        return self.controller

    def setCurrentRoutineData(self, data):
        self.currentRoutineData = data

    def getCurrentRoutineData(self):
        return self.currentRoutineData
    
    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'routinesDialog.ui'
        )
    
    def getButtonIcon(self):
        return QtGui.QIcon(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                '..',
                'icons',
                'play-button.png'
            )
        )

    def createPlayButton(self, row, col):
        wd = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(wd)
        button = QtWidgets.QPushButton('', self.tableWidget)
        button.setIcon(self.getButtonIcon())
        button.setFixedSize(QtCore.QSize(30, 30))
        button.setIconSize(QtCore.QSize(20, 20))
        index = QtCore.QPersistentModelIndex(self.tableWidget.model().index(row, col))
        button.clicked.connect(
            lambda *args, index=index: self.handlePlayBtn(index)
        )
        layout.addWidget(button)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0,0,0,0)
        return wd

    def handlePlayBtn(self, index):
        self.setCurrentRoutineData(self.getRowData(index))
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.getController().runRoutine(self.getRoutineSelected())
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        
    def addRountine(self, routineData, routineDescr, execution):
        idx = self.getRowIndex(routineDescr)
        if idx < 0:
            idx = self.tableWidget.rowCount()
            self.tableWidget.insertRow(idx)
        self.tableWidget.setItem(idx, 0, self.createNotEditableItem(json.dumps(routineData)))
        self.tableWidget.setItem(idx, 1, self.createNotEditableItem(routineDescr))
        self.tableWidget.setItem(idx, 2, self.createNotEditableItem(execution))
        self.tableWidget.setCellWidget(idx, 3, self.createPlayButton(idx, 3) )

    def addRountines(self, routines):
        self.clearAllItems()
        for routineData in routines:
            self.addRountine(
                routineData,
                routineData['description'],
                0
            )
        self.adjustColumns()
    
    def getRowIndex(self, rotinaDescr):
        for idx in range(self.tableWidget.rowCount()):
            if not (
                    rotinaDescr == self.tableWidget.model().index(idx, 1).data()
                ):
                continue
            return idx
        return -1

    def getRowData(self, modelIndex):
        return json.loads(self.tableWidget.model().index(modelIndex.row(), 0).data())

    def getColumnsIndexToSearch(self):
        return list(range(1))

    def validateValue(self, value):
        if value is None:
            return ''
        return str(value)

    def createNotEditableItem(self, value):
        item = QtWidgets.QTableWidgetItem(self.validateValue(value))
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        return item
    
    def createEditableItem(self, value):
        item = QtWidgets.QTableWidgetItem(self.validateValue(value))
        return item

    def searchRows(self, text):
        for idx in range(self.tableWidget.rowCount()):
            if text and not self.hasTextOnRow(idx, text):
                self.tableWidget.setRowHidden(idx, True)
            else:
                self.tableWidget.setRowHidden(idx, False)                

    def showErrorMessageBox(self, title, message):
        errorMessageBox = self.messageFactory.createMessage('ErrorMessageBox')
        errorMessageBox.show(self, title, message)

    def showInfoMessageBox(self, title, message):
        infoMessageBox = self.messageFactory.createMessage('InfoMessageBox')
        infoMessageBox.show(self, title, message)

    def clearAllItems(self):
        self.tableWidget.setRowCount(0)
    
    def adjustColumns(self):
        self.tableWidget.resizeColumnsToContents()

    def adjustRows(self):
        self.tableWidget.resizeRowsToContents()

    def hasTextOnRow(self, rowIdx, text):
        for colIdx in self.getColumnsIndexToSearch():
            cellText = self.tableWidget.model().index(rowIdx, colIdx).data()
            if cellText and text.lower() in cellText.lower():
                return True
        return False
    
    @QtCore.pyqtSlot(str)
    def on_searchLe_textEdited(self, text):
        self.searchRows(text)

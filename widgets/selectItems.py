from Ferramentas_Producao.widgets.widget import Widget
from Ferramentas_Producao.interfaces.IActivityDataWidget import IActivityDataWidget
import os, sys
from PyQt5 import QtWidgets, QtGui, QtCore, uic

class SelectItems(Widget, IActivityDataWidget):

    def __init__(self, title, controller=None):
        super(SelectItems, self).__init__(controller)
        uic.loadUi(self.getUiPath(), self)
        self.groupBox.setTitle(title)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'selectItems.ui'
        )

    def addItems(self, items):
        self.selectionListWidget.addItems(items)
    
    def moveSelectedItems(self, originList, destList):
        originItems = [ item for item in originList.selectedItems()]
        destItemNames = [ destList.item(idx).text() for idx in range(destList.count())]
        destList.addItems(list(set([item.text() for item in originItems]) - set(destItemNames)))
        destList.sortItems()
        [originList.takeItem(originList.row(item)) for item in originItems]

    def moveAllItems(self, originList, destList):
        originItems = [
            originList.item(idx) for idx in range(originList.count()) 
            if not originList.item(idx).isHidden()
        ]
        destItemNames = [destList.item(idx).text() for idx in range(destList.count())]
        destList.addItems(list(set([item.text() for item in originItems]) - set(destItemNames)))
        destList.sortItems()
        [originList.takeItem(originList.row(item)) for item in originItems]

    @QtCore.pyqtSlot(bool)
    def on_pushSelectionBtn_clicked(self):
        self.moveSelectedItems(self.selectionListWidget, self.shortlistWidget)
    
    @QtCore.pyqtSlot(bool)
    def on_pushAllBtn_clicked(self):
        self.moveAllItems(self.selectionListWidget, self.shortlistWidget)

    @QtCore.pyqtSlot(bool)
    def on_pullSelectionBtn_clicked(self):
        self.moveSelectedItems(self.shortlistWidget, self.selectionListWidget)

    @QtCore.pyqtSlot(bool)
    def on_pullAllBtn_clicked(self):
        self.moveAllItems(self.shortlistWidget, self.selectionListWidget)

    @QtCore.pyqtSlot(str)
    def on_searchSelectionListLe_textEdited(self, text):
        self.searchItems(self.selectionListWidget, text)

    @QtCore.pyqtSlot(str)
    def on_searchShortlistLe_textEdited(self, text):
        self.searchItems(self.shortlistWidget, text)

    def searchItems(self, itemList, text):
        for idx in range(itemList.count()):
            item = itemList.item(idx)
            if not(text.lower() in item.text()):
                item.setHidden(True)
            else:
                item.setHidden(False)

    def getSelections(self):
        return [  self.shortlistWidget.item(idx).text() for idx in range(self.shortlistWidget.count()) ]

    def reset(self):
        self.moveAllItems(self.shortlistWidget, self.selectionListWidget) 

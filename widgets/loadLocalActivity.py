from Ferramentas_Producao.widgets.widget import Widget
from Ferramentas_Producao.interfaces.IActivityDataWidget import IActivityDataWidget
import os, sys
from PyQt5 import QtWidgets, QtGui, QtCore, uic

class LoadLocalActivity(Widget, IActivityDataWidget):

    def __init__(self, controller=None):
        super(LoadLocalActivity, self).__init__(controller)
        uic.loadUi(self.getUiPath(), self)
        self.workspaceSelectItems = None
        self.layersSelectItems = None

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'loadLocalActivity.ui'
        )

    def setStyleNames(self, styleNames):
        self.stylesCb.clear()
        self.stylesCb.addItems(styleNames)

    def setWorkspaceSelectItems(self, workspaceSelectItems):
        self.workspaceSelectItems = workspaceSelectItems
        self.gridLayoutItems.addWidget(self.workspaceSelectItems, 0, 0, 1, 4)

    def setLayersSelectItems(self, layersSelectItems):
        self.layersSelectItems = layersSelectItems
        self.gridLayoutItems.addWidget(self.layersSelectItems, 1, 0, 1, 4)

    @QtCore.pyqtSlot(bool)
    def on_loadBtn_clicked(self):
        if not self.isValidInput():
            self.showErrorMessageBox(
                'Erro',
                'Selecione no mínimo uma camada!'
            )
            return
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.getController().loadActivityLayers(
                self.layersSelectItems.getSelections(),
                self.workspaceSelectItems.getSelections(),
                self.onlyGeomCbx.isChecked(),
                self.stylesCb.currentText()
            )
            self.workspaceSelectItems.reset()
            self.layersSelectItems.reset()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def isValidInput(self):
        return self.layersSelectItems.getSelections()
from PyQt5 import QtWidgets, uic, QtGui, QtCore
import os
from Ferramentas_Producao.modules.sap.widgets.sapDialog import SapDialog

class EndActivityDialog(SapDialog):

    def __init__(self, controller=None):
        super(EndActivityDialog, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.controller = controller
        self.endBtn.setEnabled(False)
        self.nameLe.textEdited.connect(self.updateEndButton)

    def setController(self, controller):
        self.controller = controller

    def getController(self):
        return self.controller
    
    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'endActivityDialog.ui'
        )
    
    def updateEndButton(self):
        if self.getController().getUserName().lower() == self.nameLe.text():
            self.endBtn.setEnabled(True)
        else:
            self.endBtn.setEnabled(False)

    @QtCore.pyqtSlot(bool)
    def on_endBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.endBtn.setEnabled(False)
        try:
            self.getController().endActivity(withoutCorrection=False)
            QtWidgets.QApplication.restoreOverrideCursor()
            self.endBtn.setEnabled(True)
            self.accept()
        except Exception as e:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.showErrorMessageBox('Erro', str(e))

    def clear(self):
        self.nameLe.setText('')
        
    def closeEvent(self, e):
        self.clear()

    
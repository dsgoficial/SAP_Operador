from PyQt5 import QtWidgets, uic, QtGui, QtCore
import os

class EndActivityDialog(QtWidgets.QDialog):

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
        if self.getController().getUserName() == self.nameLe.text():
            self.endBtn.setEnabled(True)
        else:
            self.endBtn.setEnabled(False)

    @QtCore.pyqtSlot(bool)
    def on_endBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.getController().endActivity(self.sapActivity.getId(), False)
            self.close()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def clear(self):
        self.nameLe.setText('')
        
    def closeEvent(self, e):
        self.clear()

    
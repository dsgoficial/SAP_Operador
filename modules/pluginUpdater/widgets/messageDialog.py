import os, sys
from qgis.PyQt import QtCore, uic, QtWidgets

class MessageDialog(QtWidgets.QDialog):

    def __init__(self, controller=None):
        super(MessageDialog, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.controller = controller
        #self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'message.ui'
        )

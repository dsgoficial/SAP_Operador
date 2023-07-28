from Ferramentas_Producao.interfaces.IWidget import IWidget
from PyQt5 import QtWidgets, QtGui, QtCore
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

class Widget(QtWidgets.QWidget, IWidget):

    def __init__(self, 
            controller,
            messageFactory=UtilsFactory().createMessageFactory()
        ):
        super(Widget, self).__init__()
        self.controller = controller
        self.messageFactory = messageFactory

    def setController(self, controller):
        self.controller = controller

    def getController(self):
        return self.controller

    def showErrorMessageBox(self, title, message):
        errorMessageBox = self.messageFactory.createMessage('ErrorMessageBox')
        errorMessageBox.show(self, title, message)

    def showInfoMessageBox(self, title, message):
        infoMessageBox = self.messageFactory.createMessage('InfoMessageBox')
        infoMessageBox.show(self, title, message)

    def showError(self, title, message):
        errorMessageBox = self.messageFactory.createMessage('ErrorMessageBox')
        errorMessageBox.show(self, title, message)

    def showInfo(self, title, message):
        infoMessageBox = self.messageFactory.createMessage('InfoMessageBox')
        infoMessageBox.show(self, title, message)

    def hasData(self):
        return True
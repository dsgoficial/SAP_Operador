import os, sys, copy, json
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

class SapDialog(QtWidgets.QDialog):
    
    def __init__(self,
            messageFactory=UtilsFactory().createMessageFactory()
        ):
        super(SapDialog, self).__init__()
        self.messageFactory = messageFactory
    
    def showErrorMessageBox(self, title, message):
        errorMessageBox = self.messageFactory.createMessage('ErrorMessageBox')
        errorMessageBox.show(self, title, message)

    def showInfoMessageBox(self, title, message):
        infoMessageBox = self.messageFactory.createMessage('InfoMessageBox')
        infoMessageBox.show(self, title, message)

    def showQuestionMessageBox(self, title, message):
        questionMessageBox = self.messageFactory.createMessage('QuestionMessageBox')
        return questionMessageBox.show(self, title, message)

import os
from PyQt5 import QtWidgets, uic
from SAP_Operador.modules.utils.interfaces.IMessage  import IMessage

class QuestionMessageBox(IMessage):

    def __init__(self):
        super(QuestionMessageBox, self).__init__()

    def show(self, parent, title, text):
        result = QtWidgets.QMessageBox.question(
            parent,
            title, 
            text
        )
        return result == QtWidgets.QMessageBox.Yes
import os
from PyQt5 import QtWidgets, uic
from Ferramentas_Producao.modules.utils.interfaces.IMessage  import IMessage

class QuestionMessageBox(IMessage):

    def __init__(self):
        super(QuestionMessageBox, self).__init__()

    def show(self, parent, title, text):
        QtWidgets.QMessageBox.question(
            parent,
            title, 
            text
        )
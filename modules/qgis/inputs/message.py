from SAP_Operador.modules.qgis.inputs.inputData import InputData
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets

class Message(InputData):

    def __init__(self):
        super(Message, self).__init__()
    
    def load(self, fileData):
        self.showInfoMessageBox(
            ''.join([ "<p>{0}</p>".format(e) for e in fileData])
        )
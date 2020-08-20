from Ferramentas_Producao.modules.qgis.inputs.inputData import InputData
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets
import platform

class InputLayer(InputData):

    def __init__(self, 
            groupName='MOLDURA_E_INSUMOS'
        ):
        super(InputLayer, self).__init__()
        self.groupName = groupName

    def getGroupLayer(self):
        root = core.QgsProject.instance().layerTreeRoot()
        group = root.findGroup(self.groupName)
        if not group:
            group = root.addGroup(self.groupName)
        return group
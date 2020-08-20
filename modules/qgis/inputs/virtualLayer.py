from Ferramentas_Producao.modules.qgis.inputs.inputLayer import InputLayer
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets
from qgis.PyQt.QtXml import QDomDocument

class VirtualLayer(InputLayer):

    def __init__(self):
        super(VirtualLayer, self).__init__()
    
    def load(self, data):
        layer = core.QgsProject.instance().addMapLayer(
            core.QgsVectorLayer(
                data['query'],
                data['nome'], 
                "virtual"
            ), 
            False
        )

        doc = QDomDocument()
        doc.setContent(data['qml'])
        layer.importNamedStyle(doc)
        layer.triggerRepaint()

        group = self.getGroupLayer()
        group.insertLayer(0, layer)
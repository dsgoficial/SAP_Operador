from SAP_Operador.modules.qgis.inputs.inputLayer import InputLayer
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets

class Wms(InputLayer):

    def __init__(self):
        super(Wms, self).__init__()
    
    def load(self, fileData):
        unloadedFiles = []
        #QgsRasterLayer('type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0', 'hop', 'wms')
        layer = core.QgsRasterLayer(fileData['caminho'], fileData['nome'], 'wms')
        if not layer.isValid():
            self.showErrorMessageBox(
                 '<p>erro: falha ao carregar o seguinte wms "{0}"</p>'.format(fileData['caminho'])
            )
            return

        self.addMapLayer( layer )


        
        
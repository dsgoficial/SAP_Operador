from Ferramentas_Producao.modules.qgis.inputs.inputLayer import InputLayer
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets

class Wms(InputLayer):

    def __init__(self):
        super(Wms, self).__init__()
    
    def load(self, fileData):
        unloadedFiles = []
        for d in fileData:
            #QgsRasterLayer('type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0', 'hop', 'wms')
            layer = core.QgsRasterLayer(d['caminho'], d['nome'], 'wms')
            if not layer.isValid():
                unloadedFiles.append(d)
                continue
            group = self.getGroupLayer()
            group.insertLayer(0, core.QgsProject.instance().addMapLayer(layer, False))
        if not unloadedFiles:
            return

        self.showErrorMessageBox(
            ''.join([
                '<p>erro: falha ao carregar o seguinte wms "{0}"</p>'.format(d['caminho'])
                for d in unloadedFiles
            ])
        )

        
        
from Ferramentas_Producao.modules.qgis.inputs.inputLayer import InputLayer
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets

class Wfs(InputLayer):

    def __init__(self):
        super(Wfs, self).__init__()
    
    def load(self, fileData):
        unloadedFiles = []
        for d in fileData:
            layer = core.QgsVectorLayer(d['caminho'], d['nome'], 'WFS')
            if not layer.isValid():
                unloadedFiles.append(d)
                continue
            self.addMapLayer( layer )
        if not unloadedFiles:
            return

        self.showErrorMessageBox(
            ''.join([
                    '<p>erro: falha ao carregar o seguinte wfs "{0}"</p>'.format(d['caminho'])
                    for d in unloadedFiles
            ])
        )
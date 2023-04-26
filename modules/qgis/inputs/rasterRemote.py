from Ferramentas_Producao.modules.qgis.inputs.inputRaster import InputRaster
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets
import platform

class RasterRemote(InputRaster):

    def __init__(self):
        super(RasterRemote, self).__init__()
    
    def load(self, fileData):
        if not(platform.system() == 'Windows'):
            self.showErrorMessageBox(
                '<p>erro: carregamento de raster remoto apenas no Windows</p>'
            )
            return
        if self.loadRaster(fileData['caminho'], fileData['nome'], fileData['epsg']):
            return
        self.showErrorMessageBox(''.join(
            [
                '<p>erro: falha ao carregar raster "{0}" remotamente</p>'.format(d['caminho'])
                for d in fileData
            ]
        ))
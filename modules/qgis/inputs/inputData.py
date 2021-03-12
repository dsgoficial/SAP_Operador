from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory
from qgis import utils

class InputData:

    def __init__(self,
            messageFactory=UtilsFactory().createMessageFactory()
        ):
        self.errorMessageBox = messageFactory.createMessage('ErrorMessageBox')
        self.infoMessageBox = messageFactory.createMessage('InfoMessageBox')

    def showErrorMessageBox(self, html):
        self.errorMessageBox.show(
            utils.iface.mainWindow(),
            'Erro',
            html
        )

    def showInfoMessageBox(self, html):
        self.infoMessageBox.show(
            utils.iface.mainWindow(),
            'Aviso',
            html
        )
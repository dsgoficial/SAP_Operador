from SAP_Operador.modules.utils.factories.utilsFactory import UtilsFactory
from qgis import utils

class InputData:

    def __init__(self,
            messageFactory=None,
        ):
        self.messageFactory = UtilsFactory().createMessageFactory() if messageFactory is None else messageFactory
        self.errorMessageBox = self.messageFactory.createMessage('ErrorMessageBox')
        self.infoMessageBox = self.messageFactory.createMessage('InfoMessageBox')

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
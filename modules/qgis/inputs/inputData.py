from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

class InputData:

    def __init__(self,
            messageFactory=UtilsFactory().createMessageFactory()
        ):
        self.errorMessageBox = messageFactory.createErrorMessageBox()
        self.infoMessageBox = messageFactory.createInfoMessageBox()

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
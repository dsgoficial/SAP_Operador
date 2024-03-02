
import os, sys, copy, json
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from SAP_Operador.modules.utils.factories.utilsFactory import UtilsFactory

class RasterMetadataDlg(QtWidgets.QDialog):
    def __init__(self, 
            controller=None, 
            parent=None,
            message=None,
        ):
        super(RasterMetadataDlg, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.controller = controller
        self.message = UtilsFactory().createMessageFactory() if message is None else message
        self.setup()

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'rasterMetadataDlg.ui'
        )

    def getController(self):
        return self.controller

    def showInfoMessageBox(self, message):
        messageDlg = self.message.createMessage('InfoMessageBox')
        messageDlg.show(self, 'Aviso', message)
    
    def showErrorMessageBox(self, message):
        messageDlg = self.message.createMessage('ErrorMessageBox')
        messageDlg.show(self, 'Erro', message)

    def setup(self):
        self.updateEnableBtnText()
        self.configTe.setPlaceholderText(
            '''
            EXEMPLO:

            {
                "camadas": ["[NOME-CAMADA-1]", "[NOME-CAMADA-2]", ...],
                "metadata": {
                    "[NOME-CAMADA-IMAGEM-1]": [
                        {
                            "nome": "nome-atributo",
                            "valor": "valor-atributo"
                        }
                        ...
                    ],
                    "[NOME-CAMADA-IMAGEM-2]": [
                        {
                            "nome": "nome-atributo",
                            "valor": "valor-atributo"
                        }
                        ...
                    ]
                    ...
                }
            }
            '''
        )

    def updateEnableBtnText(self):
        self.enableBtn.setText(
            'Ativar' if not self.getController().isEnabled() else 'Desativar'
        )

    def setConfig(self, data):
        self.configTe.setPlainText(data)

    @QtCore.pyqtSlot(bool)
    def on_saveConfigBtn_clicked(self):
        try:
            self.getController().setConfig(self.configTe.toPlainText())
            self.showInfoMessageBox('Salvo com sucesso!')
        except Exception as e:
            self.showErrorMessageBox(str(e))

    @QtCore.pyqtSlot(bool)
    def on_enableBtn_clicked(self):
        try:
            self.getController().setEnabled(
                bool(not self.getController().isEnabled())
            )
            self.updateEnableBtnText()
            self.showInfoMessageBox(
                'Ativado com sucesso!' if self.getController().isEnabled() else 'Desativado com sucesso!'
            )
        except Exception as e:
            self.showErrorMessageBox(str(e))
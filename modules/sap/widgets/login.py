# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
from Ferramentas_Producao.config import Config
from Ferramentas_Producao.modules.sap.interfaces.ILogin  import ILogin
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

class Login(QtWidgets.QDialog, ILogin):

    def __init__(
            self, 
            messageFactory=UtilsFactory().createMessageFactory()
        ):
        super(Login, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.setWindowTitle(Config.NAME)
        self.version_text.setText("<b>versão: {}</b>".format(Config.VERSION))
        self.controller = None
        self.messageFactory = messageFactory

    def showErrorMessageBox(self, title, message):
        errorMessageBox = self.messageFactory.createErrorMessageBox()
        errorMessageBox.show(self, title, message)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'login.ui'
        )

    def setController(self, controller):
        self.controller = controller

    def getController(self):
        if not self.controller:
            raise Exception("Controlador não foi definido!")
        return self.controller
        
    def loadData(self, user, server, password=''):
        self.userLe.setText(user) 
        self.serverLe.setText(server)  
        self.passwordLe.setText(password)

    def showView(self):
        return self.exec_()

    def closeView(self):
        self.close()

    def validInput(self):
        return ( 
            self.serverLe.text() 
            and  
            self.userLe.text() 
            and
            self.passwordLe.text()
        )

    @QtCore.pyqtSlot(bool)
    def on_submitBtn_clicked(self):
        if not self.validInput():
            html = u'<p style="color:red">Todos os campos devem ser preenchidos!</p>'
            self.showErrorMessageBox('Aviso', html)
            return
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.login()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def login(self):
        try:
            success = self.getController().authUser(
                self.userLe.text(), 
                self.passwordLe.text(), 
                self.serverLe.text()
            )
            if success:
                self.getController().saveLoginData(
                    self.userLe.text(), 
                    self.passwordLe.text(), 
                    self.serverLe.text()
                )
                self.accept()
            else:
                self.reject()
        except Exception as e:
            self.showErrorMessageBox('Erro', str(e))
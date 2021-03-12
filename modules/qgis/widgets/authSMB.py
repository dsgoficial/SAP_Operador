# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from qgis import core, gui
import sys, os
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory


class AuthSMB(QtWidgets.QDialog):

    def __init__(self, 
            parent=None,
            messageFactory=UtilsFactory().createMessageFactory()
        ):
        super(AuthSMB, self).__init__(parent)
        uic.loadUi(self.getUIPath(), self)
        self.ok_bt.clicked.connect(self.validate)
        self.cancel_bt.clicked.connect(self.reject)
        self.infoMessageBox = messageFactory.createMessage('InfoMessageBox')
        self.params = {}
        self.user = ""
        self.passwd = ""
        self.domain = ""
    
    def getUIPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis', 
            'authSMB.ui'
        )


    def validate(self):
        self.user = self.name_le.text()
        self.passwd = self.passwd_le.text()
        self.domain = self.domain_le.text()
        if self.user and self.passwd and self.domain:
            self.accept()
            return
        self.infoMessageBox.show(
            self,
            'Aviso',
            '<p>Todos os campos devem ser preenchidos!</p>'
        )

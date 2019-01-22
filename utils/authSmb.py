# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from qgis import core, gui
import sys, os

class AuthSmb(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'authSmb.ui'
    )

    def __init__(self, parent=None):
        super(AuthSmb, self).__init__(parent)
        uic.loadUi(self.dialog_path, self)
        self.ok_bt.clicked.connect(self.validate)
        self.cancel_bt.clicked.connect(self.reject)
        self.params = {}
        self.user = ""
        self.passwd = ""
        self.domain = ""

    def validate(self):
        self.user = self.name_le.text()
        self.passwd = self.passwd_le.text()
        self.domain = self.domain_le.text()
        if self.user and self.passwd and self.domain:
            self.accept()
            return
        QtGui.QMessageBox.information(
            self,
            u"Aviso", 
            u"Todos os campos devem ser preenchidos!"
        )

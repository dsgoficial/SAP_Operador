# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic, QtGui
from qgis import core, gui
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))

#carrega o arquivo da interface .ui
sys.path.append(os.path.dirname(__file__))
GUI, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__),
    'ui',
    'auth_smb.ui'), 
    resource_suffix=''
)

class Auth_Smb(QtGui.QDialog, GUI):

    def __init__(self, parent=None):
        super(Auth_Smb, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
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

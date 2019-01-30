# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, uic, QtWidgets
import os, sys


class WorksCloseDialog(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'worksCloseDialog.ui'
    )

    finish = QtCore.pyqtSignal()

    def __init__(self, user_name):
        super(WorksCloseDialog, self).__init__()
        ic.loadUi(self.dialog_path, self)
        self.user_name = user_name
        self.cancel_btn.clicked.connect(self.close)
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.close_works)
        self.name_le.textEdited.connect(self.validate)

    def validate(self, text):
        if text == self.user_name:
            self.ok_btn.setEnabled(True)
        else:
            self.ok_btn.setEnabled(False)

    def close_works(self):
        self.accept()
        self.finish.emit()
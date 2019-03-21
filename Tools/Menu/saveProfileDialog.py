# -*- coding: utf-8 -*-
import os, sys, copy
from PyQt5 import QtCore, uic, QtWidgets

class SaveProfileDialog(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'saveProfileDialog.ui'
    )

    def __init__(self, profile_name, parent):
        super(SaveProfileDialog, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.profile_name_le.setText(profile_name)
        self.parent = parent
        self.buttonBox.accepted.connect(
            self.save
        )

    def save(self):
        name = self.profile_name_le.text()
        self.parent.parent.save_profile(name)
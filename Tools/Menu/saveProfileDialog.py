# -*- coding: utf-8 -*-
import os, sys, copy
from PyQt5 import QtCore, uic, QtWidgets

class SaveProfileDialog(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'saveProfileDialog.ui'
    )

    def __init__(self, profile_name):
        super(SaveProfileDialog, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.profile_name_le.setText(profile_name)

    def get_profile_name(self):
        return self.profile_name_le.text()
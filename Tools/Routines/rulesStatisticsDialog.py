# -*- coding: utf-8 -*-
import os
from PyQt5 import QtWidgets, uic

class RulesStatisticsDialog(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'rulesStatisticsDialog.ui'
    )

    def __init__(self, html):
        super(RulesStatisticsDialog, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.textEdit.setHtml(html)
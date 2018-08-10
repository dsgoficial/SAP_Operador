# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic, QtGui, QtWebKit
import os, sys
#carrega o arquivo da interface .ui
sys.path.append(os.path.dirname(__file__))
GUI, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__),
    'ui',
    'check_finish_activity.ui'), 
    resource_suffix=''
)

class FinishActivity(QtGui.QDialog, GUI):

    finish = QtCore.pyqtSignal()

    def __init__(self, loginData):
        super(FinishActivity, self).__init__()
        self.setupUi(self)
        self.loginData = loginData
        self.cancel_btn.clicked.connect(self.close)
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.finishActivity)
        self.name_le.textEdited.connect(self.validateFinish)

    def validateFinish(self, text):
        if text == self.loginData['user']:
            self.ok_btn.setEnabled(True)
        else:
            self.ok_btn.setEnabled(False)

    def finishActivity(self):
        self.accept()
        self.finish.emit()
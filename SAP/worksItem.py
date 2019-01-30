# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from qgis import core, gui
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))


class WorksItem(QtWidgets.QWidget):

    enable_btn = QtCore.pyqtSignal()
    disable_btn = QtCore.pyqtSignal()

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'worksItem.ui'
    )

    def __init__(self, description, values_cbx, parent):
        super(WorksItem, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.parent = parent
        self.description = description
        self.values_cbx = values_cbx
        self.load_activity()

    def load_activity(self):
        self.description_lb.setText(u"<h2>{0}</h2>".format(self.description))
        for value in self.values_cbx:
            cbx = self.parent.createCheckBox(value, self.cbx_gpb)
            cbx.clicked.connect(self.validate_checkbox)

    def validate_checkbox(self):
        groupBox = self.cbx_gpb
        qnt_cbx = groupBox.children()[0].count()
        qnt_cbx_checked = 0
        for idx in range(groupBox.children()[0].count()):
            if groupBox.children()[0].itemAt(idx).widget().isChecked():
                qnt_cbx_checked += 1
        if qnt_cbx == qnt_cbx_checked:
            self.enable_btn.emit()
        else:
            self.disable_btn.emit()
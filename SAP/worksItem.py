# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from qgis import core, gui
from textwrap import wrap
import sys, os
#sys.path.append(os.path.join(os.path.dirname(__file__),'../'))


class WorksItem(QtWidgets.QWidget):

    enable_btn = QtCore.pyqtSignal()
    disable_btn = QtCore.pyqtSignal()

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'worksItem.ui'
    )

    def __init__(self, sap_data, parent):
        super(WorksItem, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.parent = parent
        self.woks_data = sap_data['dados']['atividade']
        self.description = self.woks_data['nome']
        self.values_cbx = self.woks_data['requisitos'] if 'requisitos' in self.woks_data else []
        self.observation = ''
        if 'observacao' in self.woks_data and self.woks_data['observacao']:
            self.observation = self.woks_data['observacao']
        if len(self.values_cbx) > 0:
            self.parent.close_works_btn.setEnabled(False)
        self.load_activity()

    def get_checkbox(self, name, parent):
        name = "\n".join(wrap(name))
        cbx = QtWidgets.QCheckBox(name, parent)
        parent.children()[0].addWidget(cbx)
        return cbx

    def load_activity(self):
        if self.description:
            self.description_lb.setText("<h2>{0}</h2>".format(self.description))
            self.description_lb.setWordWrap(True)
        else:
            self.observation_lb.setVisible(False)
        if self.observation:
            self.observation_lb.setText("<h2>{0}</h2>".format(self.observation))
            self.observation_lb.setWordWrap(True)
        else:
            self.observation_lb.setVisible(False)
        for obs in [ 'observacao_subfase', 'observacao_etapa', 'observacao_unidade_trabalho', 'observacao_atividade' ]:
            lb = QtWidgets.QLabel(self.woks_data[obs], self.cbx_gpb)
            self.observation_frame.layout().addWidget(lb)
        for value in self.values_cbx:
            cbx = self.get_checkbox(value, self.cbx_gpb)
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
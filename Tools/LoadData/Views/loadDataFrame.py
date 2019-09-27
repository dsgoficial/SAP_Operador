# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
from Ferramentas_Producao.utils import msgBox, cursorWait
from Ferramentas_Producao.Tools.LoadData.Views.localLayersWidget import LocalLayersWidget
from Ferramentas_Producao.Tools.LoadData.Views.remoteLayersWidget import RemoteLayersWidget

class LoadDataFrame(QtWidgets.QFrame):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'loadDataFrame.ui'
    )

    database_load = QtCore.pyqtSignal(str)
    load_data = QtCore.pyqtSignal(dict)
    menu_selected = QtCore.pyqtSignal()

    def __init__(self, iface, sap_mode=False):
        super(LoadDataFrame, self).__init__()
        self.iface = iface
        self.db_selected = None
        self.sap_mode = sap_mode
        self.layers_widget = None
        uic.loadUi(self.dialog_path, self)
        if self.sap_mode:
            self.layers_widget = RemoteLayersWidget()
        else:
            self.layers_widget = LocalLayersWidget()
        self.layers_frame.layout().addWidget(self.layers_widget)

    def config_sap_mode(self):
        self.sap_mode = True
        self.db_options.setVisible(False)
        self.db_label.setVisible(False)
    
    def load_dbs_name(self, dbs_name):
        self.db_options.addItems(dbs_name)

    def load(self, data):
        self.styles_options.clear()
        self.styles_options.addItems(data['styles'])
        self.layers_widget.load(data)
            
    @QtCore.pyqtSlot(int)
    def on_load_menu_stateChanged(self, state):
        self.menu_selected.emit() if state else ''

    @QtCore.pyqtSlot(int)
    def on_db_options_currentIndexChanged(self, idx):
        db_selected = self.db_options.currentText() if idx != 0 else ''
        if db_selected :
            cursorWait.start()
            try:
                self.db_selected = db_selected
                self.database_load.emit(db_selected)
            finally:
                cursorWait.stop()
        else:
            self.styles_options.clear()
            self.layers_widget.clean_lists() if self.layers_widget else ''
            self.db_selected = None

    def reset_load_data(self, total):
        self.progress_load.setValue(total)
        self.progress_load.setValue(0)
        self.layers_widget.restart() if self.layers_widget else ''

    def update_progressbar(self):
        self.progress_load.setValue(self.progress_load.value() + 1)

    @QtCore.pyqtSlot(bool)
    def on_load_btn_clicked(self, b):
        layers, input_files, rules, workspaces, only_with_geometry = self.layers_widget.get_inputs()
        total = len(layers+input_files)
        if self.sap_mode or (workspaces and self.db_selected):
            cursorWait.start()
            try:
                self.progress_load.setMaximum(total) if total > 0 else ''
                self.load_data.emit({
                    'workspaces' : workspaces,
                    'style_name' : self.styles_options.currentText(),
                    'with_geom' : only_with_geometry,
                    'layers_name' : layers,
                    'rules_name' : rules,
                    'input_files' : input_files
                })
                self.reset_load_data(total) if total > 0 else ''
            finally:
                cursorWait.stop()
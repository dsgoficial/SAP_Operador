# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox

class MenuConfigFrame(QtWidgets.QFrame):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'menuConfigFrame.ui'
    )
    #add_tab = QtCore.pyqtSignal(dict)
    #edit_tab = QtCore.pyqtSignal(dict)
    #remove_tab = QtCore.pyqtSignal(dict)
    #add_button = QtCore.pyqtSignal(dict)
    #edit_button = QtCore.pyqtSignal(dict)
    #remove_button = QtCore.pyqtSignal(dict)
    #save_profile = QtCore.pyqtSignal(dict)
    #update_menu = QtCore.pyqtSignal(dict)

    def __init__(self, iface):
        super(MenuConfigFrame, self).__init__()
        self.iface = iface
        uic.loadUi(self.dialog_path, self)
        self.operations =  [
            u"<Operações>",
            u"Adicionar Aba",
            u"Editar Aba",
            u"Remover Aba",
            u"Adicionar Botão",
            u"Editar Botão",
            u"Remover Botão",
        ]

    def load(self, frame_data):
        self.menu_options.clear()
        self.menu_options.addItems(frame_data['profiles_name'])

    @QtCore.pyqtSlot(int)
    def on_menu_options_currentIndexChanged(self, idx):
        self.operation_options.clear()
        profile_selected = self.menu_options.currentText() if idx != 0 else ''
        if profile_selected:      
            self.operation_options.addItems(self.operations)
      
    @QtCore.pyqtSlot(int)
    def on_operation_options_currentIndexChanged(self, idx):
        operation_selected = self.operation_options.currentText()
        self.load_table(operation_selected)

    def add_widget_on_cell(self):
        cb = QtWidgets.QComboBox(self.config_table)
        cb.addItem('12/1/12')
        self.config_table.setCellWidget(0, 1, cb)

    def clean_table(self):
        self.config_table.setRowCount(0)
        self.config_table.setColumnCount(0)

    def load_table(self, operation_selected):
        self.clean_table()
        if operation_selected == u"Adicionar Aba":
            self.config_table.setRowCount(2)
            self.config_table.setColumnCount(2)
            self.add_widget_on_cell()
        #elif operation_selected == u"Editar Aba":
        #elif operation_selected == u"Remover Aba":
        #elif operation_selected == u"Adicionar Botão":
        #elif operation_selected == u"Editar Botão":
        #elif operation_selected == u"Remover Botão": 
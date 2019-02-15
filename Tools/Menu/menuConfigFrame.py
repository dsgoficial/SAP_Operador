# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox

class MenuConfigFrame(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'menuConfigFrame.ui'
    )

    update = QtCore.pyqtSignal(dict)
    add = QtCore.pyqtSignal(dict)
    delete = QtCore.pyqtSignal(dict)
    get = QtCore.pyqtSignal(dict)

    def __init__(self, iface, parent):
        super(MenuConfigFrame, self).__init__()
        self.iface = iface
        self.parent = parent
        uic.loadUi(self.dialog_path, self)
        self.config_table.setColumnCount(2)
        self.config_table.setHorizontalHeaderLabels(['Campos', 'Valores'])
        self.config_table.horizontalHeader().setDefaultSectionSize(150)
        self.config_table.horizontalHeader().setStretchLastSection(True)
        operations =  [
            '<Operações>', 
            'Adicionar Aba', 
            'Adicionar Botão', 
            'Editar Aba', 
            'Editar Botão', 
            'Remover Aba', 
            'Remover Botão'
        ]
        self.operation_options.addItems(operations)
        self.form_values = {}

    def show_message(self):
        html="<p>Não há nenhum perfil carregado</p>"
        msgBox.show(html, "AVISO", parent=self)

    @QtCore.pyqtSlot(int)
    def on_operation_options_currentIndexChanged(self, idx):
        if idx > 0:
            self.clean_table()
            self.form_values = {}
            functions = { 
                'Adicionar Aba' : self.add_tab_form, 
                'Adicionar Botão' : self.add_btn_form,
                'Editar Aba' : self.update_tab_form,
                'Editar Botão' : self.update_btn_form,
                'Remover Aba' : self.del_tab_form,
                'Remover Botão' : self.del_btn_form
            }
            op_name = self.operation_options.currentText()
            functions[op_name]()
        else:
            self.clean_table()

    def clean_table(self):
        self.config_table.setRowCount(0)
    
    @QtCore.pyqtSlot(bool)
    def on_update_btn_clicked(self, b):
        print(self.form_values)

    @QtCore.pyqtSlot(bool)
    def on_save_btn_clicked(self, b):
        print(self.form_values)

    def get_lb(self, text):
        lb = QtWidgets.QLabel(self.config_table)
        lb.setText("<b>{0}</b>".format(text))
        return lb
    
    def get_cb(self, field_name, items=[]):
        cb = QtWidgets.QComboBox(self.config_table)
        cb.addItems(items)
        cb.setObjectName(field_name)
        cb.currentIndexChanged.connect(
            lambda: self.update_form_values(cb)
        )
        self.form_values[field_name] = cb.currentText()
        return cb

    def get_le(self, field_name, text=''):
        le = QtWidgets.QLineEdit(self.config_table)
        le.setText(text)
        le.setObjectName(field_name)
        le.textEdited.connect(
            lambda: self.update_form_values(le)
        )
        self.form_values[field_name] = le.text()
        return le
 
    def update_form_values(self, obj_input):
        field_name = obj_input.objectName()
        if type(obj_input) == QtWidgets.QComboBox:
            self.form_values[field_name] = obj_input.currentText()
        else:
            self.form_values[field_name] = obj_input.text()

    def add_tab_form(self):
        row_idx = 0
        field_name = u"Nome da Aba :"
        widget_field = self.get_lb(field_name)
        widget_input = self.get_le(field_name)
        self.config_table.insertRow(row_idx)
        self.config_table.setCellWidget(row_idx, 0, widget_field)
        self.config_table.setCellWidget(row_idx, 1, widget_input)
        
    def del_tab_form(self):
        row_idx = 0
        field_name = u"Selecione Aba :"
        widget_field = self.get_lb(field_name)
        tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
        widget_input = self.get_cb(field_name, tabs_name)
        self.config_table.insertRow(row_idx)
        self.config_table.setCellWidget(row_idx, 0, widget_field)
        self.config_table.setCellWidget(row_idx, 1, widget_input)
    
    def update_tab_form(self):
        for row_idx in range(2):
            if row_idx == 0:
                field_name = u"Selecione Aba :"
                widget_field = self.get_lb(field_name)
                tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
                widget_input = self.get_cb(field_name, tabs_name)
            else:
                field_name = u"Novo nome da Aba :"
                widget_field = self.get_lb(field_name)
                widget_input = self.get_le(field_name)
            self.config_table.insertRow(row_idx)
            self.config_table.setCellWidget(row_idx, 0, widget_field)
            self.config_table.setCellWidget(row_idx, 1, widget_input)

    def add_btn_form(self):
        for row_idx in range(2):
            if row_idx == 0:
                field_name = u"Selecione Aba :"
                widget_field = self.get_lb(field_name)
                tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
                widget_input = self.get_cb(field_name, tabs_name)
            else:
                field_name = u"Selecione Camada :"
                widget_field = self.get_lb(field_name)
                buttons_name = self.parent.get_all_buttons_name()
                widget_input = self.get_cb(field_name, buttons_name)
            self.config_table.insertRow(row_idx)
            self.config_table.setCellWidget(row_idx, 0, widget_field)
            self.config_table.setCellWidget(row_idx, 1, widget_input)
    
    def del_btn_form(self):
        for row_idx in range(2):
            if row_idx == 0:
                field_name = u"Selecione Aba :"
                widget_field = self.get_lb(field_name)
                tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
                widget_input = self.get_cb(field_name, tabs_name)
            else:
                field_name = u"Selecione Botão :"
                widget_field = self.get_lb(field_name)
                buttons_name = self.parent.get_all_tabs_name(onlyEditable=True)
                widget_input = self.get_cb(field_name, tabs_name)
            self.config_table.insertRow(row_idx)
            self.config_table.setCellWidget(row_idx, 0, widget_field)
            self.config_table.setCellWidget(row_idx, 1, widget_input)
    
    def update_btn_form(self):
        for row_idx in range(2):
            if row_idx == 0:
                field_name = u"Selecione Aba :"
                tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
                widget_input = self.get_cb(field_name, tabs_name)
                widget_input.currentIndexChanged.connect(
                    lambda : self.update_form_widgets("add btns options")
                )
            else:
                field_name = u"Selecione Botão :"
                widget_input = self.get_cb(field_name)
                widget_input.currentIndexChanged.connect(
                    lambda : self.update_form_widgets("add btn fields")
                )
            widget_label = self.get_lb(field_name)
            self.config_table.insertRow(row_idx)
            self.config_table.setCellWidget(row_idx, 0, widget_label)
            self.config_table.setCellWidget(row_idx, 1, widget_input)

    def update_form_widgets(self, tag_name):
        print(tag_name)
        col_input = 1
        tabs_options = self.config_table.cellWidget(0, col_input)
        tab_name = tabs_options.currentText()
        btns_options = self.config_table.cellWidget(1, col_input)
        if tag_name == "add btns options":
            btns_options.clear()
            btns_names = self.parent.get_all_buttons_name(tab_name)
            btns_options.addItems(["<...>"]+btns_names)
        elif tag_name == "add btn fields" and btns_options.currentIndex() > 0:
            button_name = btns_options.currentText()
            button_data = self.parent.get_button_data(tab_name, button_name)
            print(button_data['fields'])
            print(button_data['formValues'])
            is_value_map = (
                (name in layer_data['layer_fields']) and 
                (u"valueMap" in layer_data['layer_fields'][name])
            )

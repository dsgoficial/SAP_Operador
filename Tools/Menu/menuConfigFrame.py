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
        self.config_table.setColumnWidth(0, 300)
        self.config_table.setColumnWidth(1, 300)
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

    @QtCore.pyqtSlot(int)
    def on_operation_options_currentIndexChanged(self, idx):
        if idx > 0:
            self.clean_table()
            self.form_values = {}
            functions = { 
                'Adicionar Aba' : { 
                    'function' : self.load_form_tab, 
                    'tag_name' : 'add tab'
                }, 
                'Adicionar Botão' : { 
                    'function' : self.load_form_btn, 
                    'tag_name' : 'add button'
                },
                'Editar Aba' : { 
                    'function' : self.load_form_tab, 
                    'tag_name' : 'edit tab'
                },
                'Editar Botão' : { 
                    'function' : self.load_form_btn, 
                    'tag_name' : 'edit button'
                },
                'Remover Aba' : { 
                    'function' : self.load_form_tab, 
                    'tag_name' : 'del tab'
                },
                'Remover Botão' : { 
                    'function' : self.load_form_btn, 
                    'tag_name' : 'del button'
                }
            }
            op_name = self.operation_options.currentText()
            tag_name = functions[op_name]['tag_name']
            functions[op_name]['function'](tag_name)
        else:
            self.clean_table()

    def validate_form_values(self):
        fields = []
        for f in self.form_values:
            if '*' in f and not(self.form_values[f]) or '<...>' == self.form_values[f]:
                fields.append(f)
        if fields:
            html="<p>Os seguintes campos são obrigatórios(*):</p>"
            html+='\n'.join([ '<p style="color:red;">[{}]</p>'.format(f) for f in fields])
            self.show_message(html)
            return False
        return True

    def show_message(self, html):
        msgBox.show(html, "AVISO", parent=self)

    @QtCore.pyqtSlot(bool)
    def on_update_btn_clicked(self, b):
        if self.validate_form_values():
            print(self.operation_options.currentIndex())
            print(self.operation_options.currentText())
            print(self.form_values)
            """ profile_data = self.parent.load_data()
            for tab_name in reversed(profile_data['orderMenu']['orderTab']):
                self.add_tab(tab_name)
                for button_name in reversed(profile_data['orderMenu']['orderButton'][tab_name]):
                    if button_name in profile_data['perfil'][tab_name]:
                        button_data = profile_data['perfil'][tab_name][button_name]
                        self.add_button(button_data) """

    @QtCore.pyqtSlot(bool)
    def on_save_btn_clicked(self, b):
        print(self.form_values)
 
    def update_form_values(self, obj_input):
        field_name = obj_input.objectName()
        if type(obj_input) == QtWidgets.QComboBox:
            self.form_values[field_name] = obj_input.currentText()
        else:
            self.form_values[field_name] = obj_input.text()
    
    def load_form_tab(self, tag_name):
        if tag_name == 'add tab':
            field_name = u"*Nome da aba :"
            self.add_widget_cell(field_name, '', type_field='le')  
        elif tag_name == 'del tab':
            field_name = u"*Selecione aba :"
            tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
            tabs_cb = self.add_widget_cell(field_name, tabs_name, type_field='cb')
        else:
            field_name = u"*Selecione aba :"
            tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
            tabs_cb = self.add_widget_cell(field_name, tabs_name, type_field='cb')
            field_name = u"*Nome da aba :"
            self.add_widget_cell(field_name, '', type_field='le')
    
    def load_form_btn(self, tag_name):
        field_name = u"*Selecione aba :"
        tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
        tabs_cb = self.add_widget_cell(field_name, tabs_name, type_field='cb')
        if tag_name == 'add button':
            tabs_cb.currentIndexChanged.connect(
                lambda : self.update_form_widgets("add layers options")
            )
            field_name = u"*Selecione camada :"
            layers_cb = self.add_widget_cell(field_name, [], type_field='cb')
            layers_cb.currentIndexChanged.connect(
                lambda : self.update_form_widgets("add button fields")
            )
            self.update_form_widgets("add layers options")
        else:
            tabs_cb.currentIndexChanged.connect(
                lambda : self.update_form_widgets("add buttons options")
            )
            field_name = u"*Selecione botão :"
            btns_cb = self.add_widget_cell(field_name, [], type_field='cb')
            if tag_name == 'edit button':
                btns_cb.currentIndexChanged.connect(
                    lambda : self.update_form_widgets("edit button fields")
                )
            self.update_form_widgets("add buttons options")

    def update_form_widgets(self, tag_name):
        self.config_table.setRowCount(2)
        col_input = 1
        tabs_cb = self.config_table.cellWidget(0, col_input)
        tab_name = tabs_cb.currentText()
        options_cb = self.config_table.cellWidget(1, col_input)
        if tag_name in ["add buttons options", "add layers options"]:
            options_cb.clear()
            if tag_name == "add buttons options":
                names = self.parent.get_all_buttons_name(tab_name)
            else:
                names = self.parent.parent.get_layers_name()
            options_cb.addItems(["<...>"]+names)
        elif (
                tag_name in ["add button fields", "edit button fields"] 
                and options_cb.currentIndex() > 0
            ):
            if tag_name == "edit button fields":
                button_name = options_cb.currentText()
                button_data = self.parent.get_button_data(tab_name, button_name)
                layer_name = button_data['formValues']['*Selecione camada:']
            else:
                layer_name = options_cb.currentText()
                button_name = ''
                button_data = {}
            self.load_custom_fields_btn(button_name, button_data)
            self.load_fields_btn(tab_name, layer_name, button_data)

    def load_custom_fields_btn(self, button_name, button_data):
        custom_fields = [
            {
                'field_name' :  u'*Nome do botão :',
                'field_values' : button_name
            },
            {
                'field_name' :  u'Fechar form na aquisição:',
                'field_values' : [
                    u'Não',
                    u'Sim'
                ]
            },
            {
                'field_name' : u'Escolha ferramenta de aquisição:',
                'field_values' : [
                    u'Normal',
                    u'Mão livre',
                    u'Angulor reto',
                    u'Circulo'
                ]
            },
            { 
                'field_name' : u'Definir palavras chaves(separar com ";"):',
                'field_values' : ''
            }
        ]
        for field_data in custom_fields:
            field_name = field_data['field_name']
            field_values = field_data['field_values']
            type_field = 'cb' if type(field_values) == list else 'le'
            default_value = ''
            if button_data and field_name in button_data['formValues']:
                default_value = button_data['formValues'][field_name]
            self.add_widget_cell(
                field_name,
                field_values,
                type_field=type_field,
                default_value=default_value
            )

    def load_fields_btn(self, tab_name, layer_name, button_data):
        layer_data = self.parent.parent.get_layer_data(layer_name)
        layer_fields = layer_data['layer_fields']
        for field_name in layer_fields:
            if not(field_name in [
                    'filter',
                    'data_modificacao',
                    'controle_id',
                    'ultimo_usuario',
                    'id'
                ]):
                exist_field = button_data and field_name in button_data['formValues']
                default_value = ''
                if exist_field:
                    default_value = button_data['formValues'][field_name]
                if 'valueMap' in layer_fields[field_name]:
                    options_values = list(layer_fields[field_name]['valueMap'].keys())
                    options_values.append('IGNORAR')
                    options_values = list(set(options_values))
                    self.add_widget_cell(
                        field_name,
                        options_values,
                        type_field='cb',
                        default_value=default_value
                    )
                else:
                    self.add_widget_cell(
                        field_name,
                        '',
                        type_field='le',
                        default_value=default_value 
                    )

    def add_widget_cell(self, field_name, value, type_field, default_value=''):
        row_idx = self.config_table.rowCount()
        widget_label = self.get_lb(field_name)
        if type_field == 'cb':
            widget_input = self.get_cb(field_name, value)
            self.set_default_value_cb(widget_input, default_value)
        else:
            widget_input = self.get_le(field_name, value)
        if default_value and type_field == 'le':
            widget_input.setText(default_value)
        self.config_table.insertRow(row_idx)
        self.config_table.setCellWidget(row_idx, 0, widget_label)
        self.config_table.setCellWidget(row_idx, 1, widget_input)            
        return widget_input

    def set_default_value_cb(self, cb, value=''):
        if value:
            index = cb.findText( 
                value, QtCore.Qt.MatchFixedString
            )  
        else: 
            index = cb.findText(
                "A SER PREENCHIDO", QtCore.Qt.MatchFixedString
            )
        if index >= 0:
            cb.setCurrentIndex(index)

    def clean_table(self):
        self.config_table.setRowCount(0)

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
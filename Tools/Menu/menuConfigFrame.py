# -*- coding: utf-8 -*-
import os, sys, copy
from PyQt5 import QtCore, uic, QtWidgets
from .saveProfileDialog import SaveProfileDialog
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox

class MenuConfigFrame(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'menuConfigFrame.ui'
    )

    def __init__(self, iface, parent):
        super(MenuConfigFrame, self).__init__()
        self.iface = iface
        self.parent = parent
        uic.loadUi(self.dialog_path, self)
        self.config_table.setColumnCount(2)
        self.config_table.setHorizontalHeaderLabels(['Campos', 'Valores'])
        self.config_table.setColumnWidth(0, 300)
        self.config_table.setColumnWidth(1, 300)
        self.functions_map = { 
            'Adicionar Aba' : { 
                'open_form' : self.load_form_tab,
                'tag_name' : 'add',
                'run' : self.update_tab_data
            }, 
            'Adicionar Botão' : { 
                'open_form' : self.load_form_btn,
                'tag_name' : 'add',
                'run' : self.update_btn_data
            },
            'Editar Aba' : { 
                'open_form' : self.load_form_tab, 
                'tag_name' : 'edit',
                'run' : self.update_tab_data
            },
            'Editar Botão' : { 
                'open_form' : self.load_form_btn, 
                'tag_name' : 'edit',
                'run' : self.update_btn_data
            },
            'Remover Aba' : { 
                'open_form' : self.load_form_tab, 
                'tag_name' : 'del',
                'run' : self.update_tab_data
            },
            'Remover Botão' : { 
                'open_form' : self.load_form_btn, 
                'tag_name' : 'del',
                'run' : self.update_btn_data
            }
        }
        operations =  ['<Operações>']+sorted(list(self.functions_map.keys()))
        self.operation_options.addItems(operations)
        self.form_values = {}

    @QtCore.pyqtSlot(int)
    def on_operation_options_currentIndexChanged(self, idx):
        if idx > 0:
            self.clean_table()
            self.form_values = {}
            
            op_name = self.operation_options.currentText()
            tag_name = self.functions_map[op_name]['tag_name']
            self.functions_map[op_name]['open_form'](tag_name)
        else:
            self.clean_table()

    def validate_form_values(self):
        idx_oper = self.operation_options.currentIndex()
        valid = False
        if idx_oper > 0:
            fields = []
            for f in self.form_values:
                if '*' in f and not(self.form_values[f]) or '<...>' == self.form_values[f]:
                    fields.append(f)
            if fields:
                html="<p>Os seguintes campos são obrigatórios(*):</p>"
                html+='\n'.join([ '<p style="color:red;">[{}]</p>'.format(f) for f in fields])
                self.show_message(html)
            else:
                valid = True
        return valid

    def show_message(self, html):
        msgBox.show(html, "AVISO", parent=self)

    def get_template_profile_data(self):
        template = {
            "nome_do_perfil" : '',
            "perfil" : {},
            "orderMenu" : {
                'orderTab' : [],
                'orderButton' : {}
            }
        }
        return template

    def get_current_profile_data(self):
        data = self.parent.parent.load_data()
        if not(data):
            data = self.get_template_profile_data()
        return data

    def update_tab_data(self, tag_name):
        current_profile_data = self.get_current_profile_data()
        order_menu = current_profile_data['orderMenu']
        profile = current_profile_data['perfil']
        if tag_name == 'add':
            tab_name = self.form_values['*Nome da aba:']
            if not(tab_name in profile):
                profile[tab_name] = {}
                order_menu['orderTab'].append(tab_name)
                order_menu['orderButton'][tab_name] = []
        else:
            tab_name = self.form_values['*Selecione aba:']
            valid_tab = tab_name in profile
            if valid_tab and tag_name == 'del':
                del profile[tab_name]
                order_menu['orderTab'].remove(tab_name)
                del order_menu['orderButton'][tab_name]
            elif valid_tab:
                new_tab = self.form_values['*Nome da aba:']
                temp = profile[tab_name] 
                for b in temp:
                    temp[b]['formValues']['*Selecione aba:'] = new_tab
                del profile[tab_name] 
                profile[new_tab] = temp
                order_menu['orderTab'] = [
                    n.replace(tab_name, new_tab) for n in order_menu['orderTab']
                ]
                temp = order_menu['orderButton'][tab_name]
                del order_menu['orderButton'][tab_name]
                order_menu['orderButton'][new_tab] = temp
        self.parent.load_menu_profile(
            copy.deepcopy(current_profile_data)
        )
        self.clean_table()
        self.load_form_tab(tag_name)

    def update_btn_data(self, tag_name):
        current_profile_data = self.get_current_profile_data()
        order_menu = current_profile_data['orderMenu']
        profile = current_profile_data['perfil']
        tab_name = self.form_values['*Selecione aba:']
        if tag_name == 'add':
            btn_name = self.form_values['*Nome do botão:']
            valid_btn = (
                tab_name in profile
                and
                not(btn_name in profile[tab_name])
            )
            if valid_btn:
                profile[tab_name][btn_name] = {
                    'formValues' : self.form_values
                }
                order_menu['orderButton'][tab_name].append(btn_name)
        elif tag_name == 'del':
            btn_name = self.form_values['*Selecione botão:']
            valid_btn = (
                tab_name in profile
                and
                btn_name in profile[tab_name]
            )
            if valid_btn:
                del profile[tab_name][btn_name]
                order_menu['orderButton'][tab_name].remove(btn_name)
        else:
            old_name = self.form_values['*Selecione botão:']
            valid_btn = (
                tab_name in profile
                and
                old_name in profile[tab_name]
            )
            if valid_btn: 
                btn_name = self.form_values['*Nome do botão:']
                temp = profile[tab_name][old_name]
                del profile[tab_name][old_name]
                temp['formValues'].update(self.form_values)
                profile[tab_name][btn_name] = temp
                order_btn = order_menu['orderButton'][tab_name]
                order_menu['orderButton'][tab_name] = [
                    n.replace(old_name, btn_name) for n in order_btn
                ]
        self.parent.load_menu_profile(
            copy.deepcopy(current_profile_data)
        )
        if tag_name == 'del':
            self.load_form_btn("add buttons options")
        else:
            options_cb = self.config_table.cellWidget(1, 1)
            if tag_name == 'add':
                default_value = self.form_values[u"*Selecione camada:"]
                self.load_form_btn("add")
            else:
                self.load_form_btn("edit")
                default_value = btn_name
            self.set_default_value_cb(options_cb, default_value)


    @QtCore.pyqtSlot(bool)
    def on_update_btn_clicked(self, b):
        if self.validate_form_values():
            op_name = self.operation_options.currentText()
            tag_name = self.functions_map[op_name]['tag_name']
            self.functions_map[op_name]['run'](tag_name)
    
    @QtCore.pyqtSlot(bool)
    def on_save_btn_clicked(self, b):
        profile_name = self.parent.current_profile_name
        diag = SaveProfileDialog(profile_name, self)
        diag.exec_()
        
    def load_form_tab(self, tag_name):
        if tag_name == 'add':
            field_name = u"*Nome da aba:"
            self.add_widget_cell(field_name, '', type_field='le')  
        else:
            field_name = u"*Selecione aba:"
            tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
            tabs_cb = self.add_widget_cell(field_name, tabs_name, type_field='cb')
            if tag_name == 'edit':
                field_name = u"*Nome da aba:"
                self.add_widget_cell(field_name, '', type_field='le')
    
    def load_form_btn(self, tag_name):
        field_name = u"*Selecione aba:"
        tabs_name = self.parent.get_all_tabs_name(onlyEditable=True)
        tabs_cb = self.add_widget_cell(field_name, tabs_name, type_field='cb')
        if tag_name == 'add':
            tabs_cb.currentIndexChanged.connect(
                lambda : self.update_form_widgets("add layers options")
            )
            field_name = u"*Selecione camada:"
            layers_cb = self.add_widget_cell(field_name, [], type_field='cb')
            layers_cb.currentIndexChanged.connect(
                lambda : self.update_form_widgets("add button fields")
            )
            self.update_form_widgets("add layers options")
        else:
            tabs_cb.currentIndexChanged.connect(
                lambda : self.update_form_widgets("add buttons options")
            )
            field_name = u"*Selecione botão:"
            btns_cb = self.add_widget_cell(field_name, [], type_field='cb')
            if tag_name == 'edit':
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
                'field_name' :  u'*Nome do botão:',
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
                'field_name' : u"Definir palavras chaves:",
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
                field_type = [n.lower() for n in list(layer_fields[field_name].keys())]
                if 'valuemap' in field_type:
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

    def update_form_values(self, obj_input):
        field_name = obj_input.objectName()
        if type(obj_input) == QtWidgets.QComboBox:
            self.form_values[field_name] = obj_input.currentText()
        else:
            self.form_values[field_name] = obj_input.text()
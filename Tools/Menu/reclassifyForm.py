#! -*- coding: utf-8 -*-
from PyQt5 import QtCore, uic, QtWidgets, QtGui
import os, sys

class ReclassifyForm(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'reclassifyForm.ui'
    )
    
    reclassify = QtCore.pyqtSignal(dict, dict)

    def __init__(self):
        super(ReclassifyForm, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.fields = {}
        self.formValues = {}
        self.vertical_layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.ok_btn.clicked.connect(self.confirm)

    def show_form(self, button_data, layer_data, lyrs_selected):
        self.resize(700, 600)
        self.lyrs_selected = lyrs_selected
        fields = layer_data['layer_fields']
        form_values_before = button_data['formValues']
        for name in lyrs_selected:
            checkBox = self.addCheckBox(
                u'Camada : {0} >>> Quantidade de selecionados : {1}'.format(
                    name, len(lyrs_selected[name][0])
                ),
                u'{0}_cbx'.format(name)
            )
            checkBox.setChecked(True)
        for field in fields:
            if not(field in ['loadFormUi', 
                             'data_modificacao', 
                             'controle_id', 
                             'ultimo_usuario', 
                             'id']):
                if fields[field] and (u'valueMap' in fields[field]):
                    self.addComboBox({
                        'label' : field,
                        'items' : fields[field]['valueMap'].keys(),
                        'valueDefault' : form_values_before[field],
                    })
                elif not fields[field]:
                    self.addLineEdit({
                        'label' : field,
                        'valueDefault' :  u'',
                        'valueDefault' : form_values_before[field],
                    })
        self.vertical_layout.addItem(
            QtWidgets.QSpacerItem(
                20, 48, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            )
        )
        self.show()

    def confirm(self):
        self.accept()
        self.reclassify.emit(
            self.formValues, 
            self.lyrs_selected
        )

    def addLineEdit(self, data):
        horizontalLayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        label.setText(data['label'])
        horizontalLayout.addWidget(label)
        lineEdit = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        lineEdit.setText(data['valueDefault'])
        lineEdit.setObjectName(data['label'])
        lineEdit.setMaximumWidth(500)
        lineEdit.textEdited.connect(lambda:self.insertLineEditValue(lineEdit))
        self.formValues[data['label']] = u''
        horizontalLayout.addWidget(lineEdit)
        if data['valueDefault']:
            self.formValues[data['label']] = data['valueDefault']
        self.vertical_layout.addLayout(horizontalLayout)
        return lineEdit
        
    def addComboBox(self, data):
        horizontalLayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        label.setText(data['label'])
        horizontalLayout.addWidget(label)
        comboBox = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        comboBox.addItems(sorted(data['items']))
        comboBox.setObjectName(data['label'])
        comboBox.setMaximumWidth(500)
        comboBox.currentIndexChanged.connect(
            lambda:self.insertComboBoxValue(comboBox)
        )
        self.formValues[data['label']] = comboBox.currentText()
        horizontalLayout.addWidget(comboBox)
        if 'valueDefault' in data:
            index = comboBox.findText( 
                data['valueDefault'], QtCore.Qt.MatchFixedString
            )  
        else: 
            index = comboBox.findText(
                "A SER PREENCHIDO", QtCore.Qt.MatchFixedString
            )
        if index >= 0:
            comboBox.setCurrentIndex(index)
        self.vertical_layout.addLayout(horizontalLayout)
        return comboBox 

    def addCheckBox(self, checkBoxLabel, checkBoxName):
        checkBox = QtWidgets.QCheckBox(checkBoxLabel)
        checkBox.setObjectName(checkBoxName)
        checkBox.stateChanged.connect(
            lambda:self.insertCheckBoxValue(checkBox)
        )
        layout = self.selections_frame.layout()
        layout.addWidget(checkBox)
        return checkBox

    def insertLineEditValue(self, le):
        self.formValues[le.objectName()] = le.text().strip()

    def insertComboBoxValue(self, cb):
        self.formValues[cb.objectName()] = cb.currentText().strip()

    def insertCheckBoxValue(self, cb):
        self.formValues[cb.objectName()] = cb.isChecked()

    

    
        
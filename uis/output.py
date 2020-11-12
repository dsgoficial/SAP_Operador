# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'loadLocalActivity.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(571, 459)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.comboBox = QtWidgets.QComboBox(Form)
        self.comboBox.setObjectName("comboBox")
        self.gridLayout.addWidget(self.comboBox, 2, 2, 1, 1)
        self.pushButton_9 = QtWidgets.QPushButton(Form)
        self.pushButton_9.setObjectName("pushButton_9")
        self.gridLayout.addWidget(self.pushButton_9, 2, 3, 1, 1)
        self.layersWidget = SelectItems(Form)
        self.layersWidget.setObjectName("layersWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layersWidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout.addWidget(self.layersWidget, 1, 0, 1, 4)
        spacerItem = QtWidgets.QSpacerItem(331, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 0, 1, 1)
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 1, 1, 1)
        self.workspaceWidget = SelectItems(Form)
        self.workspaceWidget.setObjectName("workspaceWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.workspaceWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout.addWidget(self.workspaceWidget, 0, 0, 1, 4)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton_9.setText(_translate("Form", "Carregar"))
        self.label.setText(_translate("Form", "Estilo:"))

from selectitems import SelectItems

# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox

class ToolsDialog(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'toolsDialog.ui'
    )

    selected_option = QtCore.pyqtSignal(dict)
    enable_action = QtCore.pyqtSignal()

    def __init__(self, iface):
        super(ToolsDialog, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.iface = iface
        self.frame = None
        self.grid = None
        self.grid = QtWidgets.QGridLayout(self.tools_area)
        self.installEventFilter(self)
        self.connect_signals()
        
    def connect_signals(self):
        self.controller_btn.clicked.connect(
            self.handler_options_btn
        )
        self.load_btn.clicked.connect(
            self.handler_options_btn
        )
        self.rotines_btn.clicked.connect(
            self.handler_options_btn
        )
        
    def handler_options_btn(self):
        button_name = self.sender().text()
        self.selected_option.emit({
            'name' : button_name
        })

    def clean_layout(self):
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)

    def show_frame(self, frame):
        self.clean_layout()
        self.frame = frame
        self.grid.addWidget(self.frame)

    def closeEvent(self, e):
        self.enable_action.emit()

    def eventFilter(self, source , event):
        if event.type() in [QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease] and event.key() == QtCore.Qt.Key_Escape:
            self.enable_action.emit()
        return super(QtWidgets.QDialog, self).eventFilter(source, event)

    def showEvent(self, e):
        self.load_btn.click() 

    def show_(self):
        self.show()
        self.raise_()
        self.activateWindow()

        
    


    
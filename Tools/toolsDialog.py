# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox
from utils.shortcutsDialog import ShortcutsDialog

class ToolsDialog(QtWidgets.QMainWindow):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'toolsDialog.ui'
    )

    selected_option = QtCore.pyqtSignal(dict)
    closed_tools_dialog = QtCore.pyqtSignal()

    def __init__(self, iface):
        super(ToolsDialog, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.iface = iface
        self.frame = None
        self.grid = None
        self.grid = QtWidgets.QGridLayout(self.tools_area)
        self.installEventFilter(self)
        toolbar = QtWidgets.QToolBar()
        button_action = QtWidgets.QAction("Atalhos", self)
        button_action.triggered.connect(self.show_shortcuts_dialog)
        toolbar.addAction(button_action)
        self.addToolBar(toolbar)
        self.connect_signals()
        
    def show_shortcuts_dialog(self, s):
        self.shortcutDlg = ShortcutsDialog()
        self.shortcutDlg.show()
        
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
        if self.sender() is None:
            return
        button_name = self.sender().objectName()
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
        self.closed_tools_dialog.emit()

    def eventFilter(self, source , event):
        if event.type() in [QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease] and event.key() == QtCore.Qt.Key_Escape:
            self.closed_tools_dialog.emit()
            self.close()
        return super(QtWidgets.QMainWindow, self).eventFilter(source, event)

    def show_(self):
        self.show()
        self.raise_()
        self.activateWindow()

        
    


    
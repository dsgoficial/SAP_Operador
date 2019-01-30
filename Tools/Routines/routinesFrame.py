# -*- coding: utf-8 -*-
import os, sys, json
from PyQt5 import QtCore, uic, QtWidgets
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox, cursorWait

class RoutinesFrame(QtWidgets.QFrame):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'routinesFrame.ui'
    )

    load_routines = QtCore.pyqtSignal(str)
    run_routine = QtCore.pyqtSignal(dict)

    def __init__(self, iface):
        super(RoutinesFrame, self).__init__()
        self.iface = iface
        uic.loadUi(self.dialog_path, self)
        self.routines_spacer = False

    def config_sap_mode(self):
        self.server_label.setVisible(False)
        self.server_input.setVisible(False)
        self.load_btn.setVisible(False)

    @QtCore.pyqtSlot(bool)
    def on_load_btn_clicked(self, b):
        self.load_routines.emit(
            self.server_input.text()
        )

    @QtCore.pyqtSlot(bool)
    def on_run_btn_clicked(self, b):
        routine_data = self.get_selected_routines()
        if routine_data:
            self.routines_progress.setMaximum(100)
            self.routines_progress.setValue(50)
            self.run_routine.emit(routine_data)
            self.routines_progress.setValue(0)

    @QtCore.pyqtSlot(str)
    def on_server_input_textEdited(self, t):
        pass

    def show_all_routines(self):
        layout = self.routines_area.layout()
        for idx in range(layout.count()):
            if type(layout.itemAt(idx)) == QtWidgets.QWidgetItem:
                layout.itemAt(idx).widget().setVisible(True)
            
    @QtCore.pyqtSlot(str)
    def on_search_input_textEdited(self, t):
        self.show_all_routines()
        if t:
            layout = self.routines_area.layout()
            for idx in range(layout.count()):
                if type(layout.itemAt(idx)) == QtWidgets.QWidgetItem:
                    routine_descr = layout.itemAt(idx).widget().text()
                    if not(t.lower() in routine_descr.lower()):
                        layout.itemAt(idx).widget().setVisible(False)

    def get_selected_routines(self):
        area = self.routines_area
        for idx in range(area.children()[0].count()):
            if area.children()[0].itemAt(idx).widget().isChecked():
                routine_data = json.loads(
                    area.children()[0].itemAt(idx).widget().routine_data
                )
                return routine_data

    def create_radio_btn(self, name, parent):
        r_btn = QtWidgets.QRadioButton(name, parent)
        parent.children()[0].addWidget(r_btn)
        return r_btn

    def load(self, routines_data):
        self.clean()
        all_routines = [
            routines_data['fme'],
            routines_data['local']
        ]
        for routines in all_routines:
            for rf in routines:
                radio_btn = self.create_radio_btn(
                    rf['description'],
                    self.routines_area
                )
                radio_btn.routine_data = json.dumps(rf)
        self.routines_spacer = QtWidgets.QSpacerItem(
            20, 
            40, 
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        self.routines_area.layout().addItem(
            self.routines_spacer
        )

    def clean(self):
        layout = self.routines_area.layout()
        for idx in range(layout.count()):
            if type(layout.itemAt(idx).widget()) == QtWidgets.QPushButton:
                layout.itemAt(idx).widget().deleteLater()
        layout.removeItem(self.routines_spacer) if self.routines_spacer else ''
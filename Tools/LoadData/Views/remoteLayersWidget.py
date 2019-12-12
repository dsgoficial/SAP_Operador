# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets

class RemoteLayersWidget(QtWidgets.QWidget):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'remoteLayersWidget.ui'
    )

    def __init__(self):
        super(RemoteLayersWidget, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.buttons = [
            self.call_all_btn_2,
            self.call_selected_btn_2,
            self.send_all_btn_2,
            self.send_selected_btn_2,
            self.call_all_btn_3,
            self.call_selected_btn_3,
            self.send_all_btn_3,
            self.send_selected_btn_3
        ]
        self.searchs = [
            self.search_all_files,
            self.search_selected_files,
            self.search_all_layers,
            self.search_selected_layers,
            self.search_all_rules,
            self.search_selected_rules

        ]
        for btn in self.buttons:
            btn.clicked.connect(self.move_items)
        for search in self.searchs:
            search.textEdited.connect(self.search_list)
    
    def get_inputs(self):
        layers = [ 
            self.layers_list_input.item(i).text() 
            for i in range(self.layers_list_input.count())
        ]
        input_files = [ 
            self.files_list_input.item(i).text() 
            for i in range(self.files_list_input.count())
        ]
        rules = [ 
            self.rules_list_input.item(i).text() 
            for i in range(self.rules_list_input.count())
        ]
        workspaces = [ ]
        only_with_geometry = self.only_geometry.isChecked()
        return layers, input_files, rules, workspaces, only_with_geometry

    def restart(self):
        for i in [self.call_all_btn_2, self.call_all_btn_3]:
            self.move_items(i.objectName())

    def clean_lists(self):
        self.layers_list.clear()
        self.files_list.clear()
        self.rules_list.clear()

    def load(self, data):
        self.clean_lists()
        self.rules_list.addItems(data['rules'])
        self.layers_list_input.addItems(data['layers'])
        self.files_list.addItems(data['input_files'])
    
    def move_all_items(self, list_origin, list_destination):
        items_origin = [
            list_origin.item(x) for x in range(list_origin.count()) if not list_origin.item(x).isHidden()
        ]
        items_destination = [
            list_destination.item(x) for x in range(list_destination.count())
        ]
        items = list(
            set([i.text() for i in items_origin]) - set([i.text() for i in items_destination])
        )
        list_destination.addItems(items)
        list_destination.sortItems()
        [list_origin.takeItem(list_origin.row(i)) for i in items_origin]

    def move_selected_items(self, list_origin, list_destination):
        items_origin = [
            item for item in list_origin.selectedItems()
        ]
        items_destination = [
            list_destination.item(x) for x in range(list_destination.count())
        ]
        items = list(
            set([i.text() for i in items_origin]) - set([i.text() for i in items_destination])
        )
        list_destination.addItems(items)
        list_destination.sortItems()
        [list_origin.takeItem(list_origin.row(i)) for i in items_origin]

    def move_items(self, name=None):
        obj_name = self.sender().objectName() if not(name) else name
        op = obj_name.split('_')[-1]
        mode = obj_name.split('_')[1]
        cmd = obj_name.split('_')[0]
        if op == '1':
            origin, destination = ([self.layers_list, self.layers_list_input]
                if cmd == 'send' else [self.layers_list_input, self.layers_list]
            )
        elif op == '2':
            origin, destination = ([self.rules_list, self.rules_list_input]
                if cmd == 'send' else [self.rules_list_input, self.rules_list]
            )
        else:
            origin, destination = ([self.files_list, self.files_list_input]
                if cmd == 'send' else [self.files_list_input, self.files_list]
            )
        if mode == 'all':
            self.move_all_items(origin, destination)
        else:
            self.move_selected_items(origin, destination)

    def search_list(self, text):
        obj_name = self.sender().objectName()
        option = obj_name.split('_')[-1]
        mode = obj_name.split('_')[1]
        if option == 'layers':
            list_items = (
                self.layers_list if mode == 'all' 
                else self.layers_list_input
            )
        elif option == 'rules':
            list_items = (
                self.rules_list if mode == 'all' 
                else self.rules_list_input
            )
        else:
            list_items = (
                self.files_list if mode == 'all' 
                else self.files_list_input
            )
        items = [
            list_items.item(x) for x in range(list_items.count())
        ]
        for item in items:
            if not(text.lower() in item.text()):
                item.setHidden(True)
            else:
                item.setHidden(False)
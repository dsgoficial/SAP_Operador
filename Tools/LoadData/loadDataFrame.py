# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox, cursorWait

class LoadDataFrame(QtWidgets.QFrame):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'loadDataFrame.ui'
    )

    database_load = QtCore.pyqtSignal(str)
    load_data = QtCore.pyqtSignal(dict)

    def __init__(self, iface):
        super(LoadDataFrame, self).__init__()
        self.iface = iface
        self.db_selected = None
        self.sap_mode = False
        uic.loadUi(self.dialog_path, self)
        self.btns = [
            self.call_all_btn_1,
            self.call_all_btn_2,
            self.call_all_btn_3,
            self.send_all_btn_1,
            self.send_all_btn_2,
            self.send_all_btn_3,
            self.call_selected_btn_1,
            self.call_selected_btn_2,
            self.call_selected_btn_3,
            self.send_selected_btn_1,
            self.send_selected_btn_2,
            self.send_selected_btn_3
        ]
        for btn in self.btns:
            btn.clicked.connect(self.move_items)
        searchs = [
            self.search_all_layers,
            self.search_selected_layers,
            self.search_all_rules,
            self.search_selected_rules,
            self.search_all_files,
            self.search_selected_files
        ]
        for search in searchs:
            search.textEdited.connect(self.search_list)

    def config_sap_mode(self):
        self.sap_mode = True
        self.db_options.setVisible(False)
        self.db_label.setVisible(False)
        self.workspace_options.setVisible(False)
        self.workspace_label.setVisible(False)
        self.send_all_btn_1.click()
        self.send_all_btn_2.click()
        self.send_all_btn_3.click()
        for btn in self.btns:
            btn.setEnabled(False)

    def load_dbs_name(self, dbs_name):
        self.db_options.addItems(dbs_name)

    def load(self, frame_data):
        self.rules_list.clear()
        self.rules_list.addItems(frame_data['rules'])
        self.workspace_options.clear()
        self.workspace_options.addItems(frame_data['workspaces'])
        self.layers_list.clear()
        self.layers_list.addItems(frame_data['layers'])
        self.styles_options.clear()
        self.styles_options.addItems(frame_data['styles'])
        self.files_list.clear()
        self.files_list.addItems(frame_data['input_files'])

    @QtCore.pyqtSlot(int)
    def on_db_options_currentIndexChanged(self, idx):
        db_selected = self.db_options.currentText() if idx != 0 else ''
        if db_selected :
            cursorWait.start()
            self.db_selected = db_selected
            self.database_load.emit(db_selected)
            cursorWait.stop()
        else:
            self.rules_list.clear()
            self.workspace_options.clear()
            self.layers_list.clear()
            self.styles_options.clear()
            self.files_list.clear()
            self.db_selected = None

    def reset_load_data(self, total):
        self.progress_load.setValue(total)
        self.progress_load.setValue(0)
        if not(self.sap_mode):
            for i in [self.call_all_btn_1, self.call_all_btn_2, self.call_all_btn_3]:
                self.move_items(i.objectName())

    def update_progressbar(self):
        self.progress_load.setValue(self.progress_load.value() + 1)

    @QtCore.pyqtSlot(bool)
    def on_load_btn_clicked(self, b):
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
        load_menu = self.load_menu.isChecked()
        total = len(layers+input_files)
        workspace_name = self.workspace_options.currentText()
        if self.sap_mode or (workspace_name and self.db_selected):
            cursorWait.start()
            self.progress_load.setMaximum(total) if total > 0 else ''
            self.load_data.emit({
                'workspace_name' : workspace_name,
                'style_name' : self.styles_options.currentText(),
                'with_menu' : load_menu,
                'with_geom' : self.only_geometry.isChecked(),
                'layers_name' : layers,
                'rules_name' : rules,
                'input_files' : input_files
            })
            self.reset_load_data(total) if total > 0 else ''
            cursorWait.stop()

    def move_all_items(self, list_origin, list_destination):
        items_origin = [
            list_origin.item(x) for x in range(list_origin.count())
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
            if not(text in item.text()):
                item.setHidden(True)
            else:
                item.setHidden(False)
    
    def show_erro(self, erro):
        html=u"<p>Erro em carregar os seguintes arquivos:</p>"
        p = u"<p>{0}</p>"
        for e in erro:
            html += p.format(e)
        msgBox.show(
            text=html, 
            title=u"Error", 
            status='critical', 
            parent=self
        )
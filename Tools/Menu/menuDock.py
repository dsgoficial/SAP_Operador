# -*- coding: utf-8 -*-
import os, sys, copy
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from .menuConfigFrame import MenuConfigFrame
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox, cursorWait

class MenuDock(QtWidgets.QDockWidget):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'menuDock.ui'
    )

    icon_path = os.path.join(
        os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            "..", 
            ".."
        )),
        'icons',
        'menu_config.png'
    )

    active_button = QtCore.pyqtSignal(dict)

    def __init__(self, iface, parent):
        super(MenuDock, self).__init__()
        self.iface = iface
        self.parent = parent
        self.sap_mode = False
        self.current_profile_name = ""
        uic.loadUi(self.dialog_path, self)
        self.menu_area_buttons.setTabPosition(QtWidgets.QTabWidget.West)
        self.menu_area_buttons.setElideMode(QtCore.Qt.ElideNone)
        self.menu_area_buttons.setStyleSheet(
            "QTabBar::tab::disabled {width: 0; heigth: 0; margin: 0; padding: 0; border: none;}"
        )
        self.menu_search.mousePressEvent = lambda _ : self.menu_search.selectAll()
        self.config_btn.setIcon(QtGui.QIcon(self.icon_path))
        self.config_btn.setIconSize(QtCore.QSize(30, 30))

    @QtCore.pyqtSlot(str)
    def on_menu_search_textEdited(self, text):
        buttons = self.get_all_buttons_tab(u'**Pesquisa**')
        if text:
            self.show_tab_search()
            for button_name in  buttons:
                button_widget = buttons[button_name]
                button_widget.hide()
                geom_btn = button_widget.button_data['formValues'][u'*Selecione camada:'][-1:]
                lyr = self.iface.activeLayer()
                geom_lyr = lyr.name()[-1:] if lyr else '' 
                word_list = [
                    w.lower() for w in 
                    button_widget.button_data['formValues'][u'Definir palavras chaves(separar com ";"):'].split(';')
                ]
                validate_with_geom = (
                    (geom_lyr.lower() in geom_btn.lower()) and 
                    (
                        text.lower() in button_name.lower() 
                        or
                        text.lower() in word_list
                    )
                )
                validate_without_geom = (
                    text.lower() in button_name.lower() 
                    or
                    text.lower() in word_list
                )
                validate_button = validate_with_geom if geom_lyr else validate_without_geom
                if validate_button:
                    button_widget.show()
        else:
            self.hide_tab_search()
    
    def show_tab_search(self):
        self.menu_area_buttons.setTabEnabled(0, True)
        self.menu_area_buttons.setCurrentIndex(0)

    def hide_tab_search(self):
        self.menu_area_buttons.setTabEnabled(0, False)
        self.menu_area_buttons.setCurrentIndex(1)

    def config_sap_mode(self):
        self.db_label.setVisible(False)
        self.workspace_label.setVisible(False)
        self.workspace_options.setVisible(False)
        self.db_options.setVisible(False)
        self.sap_mode = True
        
    def load_dbs_name(self, dbs_options):
        self.db_options.addItems(dbs_options)

    @QtCore.pyqtSlot(bool)
    def on_config_btn_clicked(self, b):
        self.menu_config = MenuConfigFrame(self.iface, self)
        self.menu_config.exec_()

    @QtCore.pyqtSlot(int)
    def on_db_options_currentIndexChanged(self, idx):
        db_selected = self.db_options.currentText() if idx != 0 else ''
        if db_selected :
            cursorWait.start()
            try:
                db_data = self.parent.get_db_data(db_selected)
                self.load(db_data)
                self.config_btn.setEnabled(True)
            finally:
                cursorWait.stop()
        else:
            self.workspace_options.clear()
            self.menu_options.clear()
            self.clean_menu()
            self.config_btn.setEnabled(False)

    def load(self, data):
        if not(self.sap_mode):
            self.workspace_options.addItems(data['workspaces_name'])
        self.menu_options.addItems(data['profiles_name'])

    def show_menu(self):
        self.iface.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)

    def save_profile(self, profile_name):
        result = self.parent.save_profile_on_db(profile_name)
        if result:
            idx = self.menu_options.findText(
                profile_name,
                QtCore.Qt.MatchFixedString
            )
            if idx < 0:
                idx = 1
                self.menu_options.insertItem(idx, profile_name)
            self.menu_options.setCurrentIndex(idx)
            html="<p>Salvo com sucesso!</p>"
        else:
            html="<p>Erro ao salvar!</p>"
        self.menu_config.show_message(html)

    @QtCore.pyqtSlot(int)
    def on_menu_options_currentIndexChanged(self, idx):
        profile_selected = self.menu_options.currentText() if idx != 0 else ''
        if profile_selected:
            profile_data = self.parent.get_profile_data(profile_selected)
            self.load_menu_profile(profile_data)
            self.current_profile_name = profile_selected
        else:
            self.clean_menu()
            self.current_profile_name = ""
            self.parent.dump_data({})

    def load_menu_profile(self, profile_data):
        self.clean_menu()
        for tab_name in reversed(profile_data['orderMenu']['orderTab']):
            self.add_tab(tab_name)
            for button_name in reversed(profile_data['orderMenu']['orderButton'][tab_name]):
                if button_name in profile_data['perfil'][tab_name]:
                    button_data = profile_data['perfil'][tab_name][button_name]
                    self.add_button(button_data)
        self.parent.dump_data(profile_data)
        self.add_tab_search(profile_data)
        
    def add_tab_search(self, profile_data):
        self.add_tab(u'**Pesquisa**')
        for tab_name in reversed(profile_data['orderMenu']['orderTab']):
            for button_name in reversed(profile_data['orderMenu']['orderButton'][tab_name]):
                if button_name in profile_data['perfil'][tab_name]:
                    button_data = copy.deepcopy(
                        profile_data['perfil'][tab_name][button_name]
                    ) 
                    button_data['formValues'][u'*Selecione aba:'] = u'**Pesquisa**'
                    self.add_button(button_data)

    def add_tab(self, tab_name):
        tab = QtWidgets.QWidget()
        layout_tab = QtWidgets.QVBoxLayout(tab)
        layout_tab.setObjectName(u'area')
        scroll = QtWidgets.QScrollArea(tab)
        scroll.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        scroll_widget.setGeometry(QtCore.QRect(0, 0, 328, 386))
        scroll_widget.setObjectName(u'scroll')
        layout_button = QtWidgets.QVBoxLayout(scroll_widget)
        layout_button.setObjectName(u'layout')
        scroll.setWidget(scroll_widget)
        layout_tab.addWidget(scroll)
        if tab_name == u'**Pesquisa**':
            if u'**Pesquisa**' in self.get_all_tabs_name():
                self.remove_tab(u'**Pesquisa**')
            else:
                self.menu_area_buttons.insertTab(0, tab, tab_name)
                self.menu_area_buttons.setTabEnabled(0, False)
        else:
            self.menu_area_buttons.insertTab(1, tab, tab_name)
        self.menu_area_buttons.setCurrentIndex(1)

    def get_all_tabs_map(self):
        tabs = {}
        for idx in range(self.menu_area_buttons.count()):
            tabs[self.menu_area_buttons.tabText(idx)] = idx
        return tabs
    
    def get_all_tabs_name(self, onlyEditable=False):
        tabs_name = list(self.get_all_tabs_map().keys())
        if onlyEditable and tabs_name:
            tabs_name.remove(u'**Pesquisa**')
        return sorted(tabs_name)
            
    def remove_tab(self, tab_name):
        tabs_map = self.get_all_tabs_map()
        self.menu_area_buttons.removeTab(tabs_map[tab_name])
    
    def get_tab_widgets(self, tab_name):
        tabs_map = self.get_all_tabs_map()
        tab_scroll = self.menu_area_buttons.widget(
            tabs_map[tab_name]
        ).findChildren(QtWidgets.QScrollArea)[0].children()[0].children()[0]
        tab_layout = tab_scroll.children()[0]
        return {
            'scroll' : tab_scroll,
            'layout' : tab_layout,
        }
             
    def get_all_buttons_tab(self, tab_name):
        buttons = {}
        if tab_name:
            tab_widgets = self.get_tab_widgets(tab_name)
            for idx in range(tab_widgets['layout'].count()):
                button_name = tab_widgets['layout'].itemAt(idx).widget().objectName()
                button_widget = tab_widgets['layout'].itemAt(idx).widget()
                buttons[button_name] = button_widget
        return buttons

    def get_button_data(self, tab_name, btn_name):
        btns_widgets = self.get_all_buttons_tab(tab_name)
        btn_widget = btns_widgets[btn_name]
        return btn_widget.button_data

    def get_all_buttons_name(self, tab_name):
        buttons_widgets = self.get_all_buttons_tab(tab_name)
        return sorted(list(buttons_widgets.keys()))

    def add_button(self, button_data):
        button_name = button_data[u'formValues'][u'*Nome do botão:']
        tab_name = button_data[u'formValues'][u'*Selecione aba:']
        layer_name = button_data[u'formValues'][u'*Selecione camada:']
        tab_data = self.get_tab_widgets(tab_name)
        tab_scroll = tab_data['scroll']
        tab_layout = tab_data['layout']
        count = tab_layout.count()
        button = QtWidgets.QPushButton(tab_scroll)
        button.setStyleSheet(
            self.get_button_style(layer_name)
        )
        button.button_data = button_data
        tab_layout.addWidget(button)
        if count >=0 and count <= 8:
            button.setText("{0}_[{1}]".format(button_name, count+1))
            button.setShortcut(
                self.get_button_shortcut(count)
            )
        else:
            button.setText(button_name)
        button.setObjectName(button_name)
        button.clicked.connect(self.run_button)

    def run_button(self):
        cursorWait.start()
        try:
            button = self.sender()
            self.reload_button_style()
            layer_name = button.button_data[u'formValues'][u'*Selecione camada:']
            button.setStyleSheet(
                self.get_button_style(layer_name, default=False)
            )
            self.active_button.emit({
                "button_data" : button.button_data,
                "reclassify" : self.menu_reclassify.isChecked(),
                "settings_user" : {
                    "db_name" : self.db_options.currentText(),
                    "workspace_name" : self.workspace_options.currentText()
                }
            })
        finally:
            cursorWait.stop()

    def reload_button_style(self):
        for tab_name in self.get_all_tabs_name():
            buttons = self.get_all_buttons_tab(tab_name)
            for button_name in buttons:
                button = buttons[button_name]
                layer_name = button.button_data[u'formValues'][u'*Selecione camada:']
                button.setStyleSheet(
                    self.get_button_style(layer_name)
                )
    
    def clean_menu(self):
        for tab_name in self.get_all_tabs_name():
            self.remove_tab(tab_name)

    def get_button_shortcut(self, no):
        shortcuts = {
            0 : QtCore.Qt.Key_1,
            1 : QtCore.Qt.Key_2,
            2 : QtCore.Qt.Key_3,
            3 : QtCore.Qt.Key_4,
            4 : QtCore.Qt.Key_5,
            5 : QtCore.Qt.Key_6,
            6 : QtCore.Qt.Key_7,
            7 : QtCore.Qt.Key_8,
            8 : QtCore.Qt.Key_9
        }
        return shortcuts[no]

    def get_button_style(self, layer_name, default=True):
        click_styles = {
            'a' : '''color: rgb(255, 255, 255);
                   background-color: rgb(255, 128, 0);''', 
            'c' : '''background-color: rgb(255, 128, 0);''',
            'p' : '''color: rgb(255, 255, 255);
                   background-color: rgb(255, 128, 0);''', 
            'd' : '''background-color: rgb(255, 128, 0);''',
            'l' : '''background-color: rgb(21, 7, 7);
                   color: rgb(255, 128, 0);''',
        }
        default_styles = {
            'a' : "color: rgb(255, 255, 255); \
                  background-color: rgb(246, 13, 13);", 
            'c' : "background-color: rgb(85, 255, 0);",
            'p' : "color: rgb(255, 255, 255); \
                  background-color: rgb(0, 0, 255);", 
            'd' : "background-color: rgb(255, 255, 0);",
            'l' : "background-color: rgb(21, 7, 7); \
                  color: rgb(255, 255, 255);",
        }
        if default:
            return default_styles[layer_name.split('_')[-1]]
        return click_styles[layer_name.split('_')[-1]]       

    
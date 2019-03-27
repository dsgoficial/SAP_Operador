# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox, cursorWait

class LoginDialog(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'loginDialog.ui'
    )

    login_remote = QtCore.pyqtSignal(dict)
    login_local = QtCore.pyqtSignal(dict)

    def __init__(self, iface):
        super(LoginDialog, self).__init__()
        self.iface = iface
        uic.loadUi(self.dialog_path, self)
        self.version_text.setText(u"<b>versão: 3.1.7</b>")
        
    @QtCore.pyqtSlot(int)
    def on_localhost_check_stateChanged(self, state):
        self.login_frame.hide() if state else self.login_frame.show()
        self.version_text.setVisible(not(state))

    def load_login_data(self, server, user, password):
        self.server_input.setText(server)  
        self.user_input.setText(user) 
        self.password_input.setText(password)

    def validate_form(self):
        test = ( 
            self.server_input.text() 
            and  
            self.user_input.text() 
            and 
            self.password_input.text() 
        )
        return test

    def show_(self):
        self.show()
        self.raise_()
        self.activateWindow()

    @QtCore.pyqtSlot(bool)
    def on_ok_btn_clicked(self):
        if self.localhost_check.isChecked():
            data = {}
        elif self.validate_form():
            data = {
                'server' : self.server_input.text(),
                'user' : self.user_input.text(),
                'password' : self.password_input.text()
            }
        else:
            html = u'<p style="color:red">Todos os campos devem ser preenchidos!</p>'
            msgBox.show(text=html, title=u"Aviso", parent=self)
            return
        cursorWait.start()
        try:
            if data:
                self.login_remote.emit(data)
            else:
                self.login_local.emit(data)
        finally:
            cursorWait.stop()
        


    
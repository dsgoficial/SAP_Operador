# -*- coding: utf-8 -*-
from PyQt5 import QtCore
import sys, os, pickle
from .worksFrame import WorksFrame
from .Login.login import Login
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import network, msgBox, managerQgis


class ManagerSAP(QtCore.QObject):

    show_tools = QtCore.pyqtSignal(bool)

    def __init__(self, iface):
        super(ManagerSAP, self).__init__()
        self.path_data = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.pickle')
        self.frame = None
        self.iface = iface
        self.login_sap = Login(self.iface)
        self.login_sap.sap.connect(
            self.login
        )
        self.login_sap.local.connect(
            self.show_tools.emit
        )
        self.net = network
        self.net.CONFIG['parent'] = self.login_sap.dialog

    def add_action_qgis(self, b):
        if b:
            self.login_sap.action.add_on_qgis()
        else:
            self.login_sap.action.remove_from_qgis()

    def enable_action_qgis(self, b):
        self.login_sap.action.setEnabled(b)
        
    def login(self, server, user, password):
        sucess = False
        post_data = {
            u"usuario" : user,
            u"senha" : password
        }
        url = u"{0}/login".format(server)
        response = self.net.POST(server, url, post_data)
        if response and response.json()['sucess']:
            token = response.json()['dados']['token']
            header = {'authorization' : token}
            url = u"{0}/distribuicao/verifica".format(server)
            response = self.net.GET(server, url, header)
            if response:
                data = response.json()
                if "dados" in data:
                    self.update_sap_data(
                        data, 
                        server, 
                        user, 
                        password, 
                        token
                    )
                    self.dump_data(data)
                    sucess = True
                else:
                    sucess = self.init_works(server, user, password, token)
        if sucess:
            self.login_sap.dialog.accept()
            self.show_tools.emit(True)


    def get_frame(self):
        self.frame = WorksFrame()
        self.frame.load(self.load_data())
        self.frame.close_works.connect(
            self.close_works
        )
        return self.frame

    def update_sap_data(self, data, server, user, password, token):
        data['token'] = token
        data['server'] = server
        data['user'] = user
        data['password'] = password
        activity = data['dados']['atividade']['nome']
        managerQgis(self.iface).save_project_var(
            'atividade', 
            activity
        )

    def init_works(self, server, user, password, token):
        result = self.show_message("new activity")
        if result == 16384:
            header = {'authorization' : token}
            url = u"{0}/distribuicao/inicia".format(server)
            response = self.net.POST(server, url, header=header)
            data = response.json()
            if data['sucess']:
                self.update_sap_data(
                    data, 
                    server, 
                    user, 
                    password, 
                    token
                )
                self.dump_data(data)
                return True
            self.show_message("no activity")
            return False

    def close_works(self):
        sap_data = self.load_data()
        works_data = sap_data['dados']['atividade']
        unit_id = works_data['unidade_trabalho_id']
        fase_id = works_data['subfase_etapa_id']
        server = sap_data['server']
        token = sap_data['server']
        user = sap_data['user']
        password = sap_data['password']
        post_data = {
            'subfase_etapa_id' : fase_id,
            'unidade_trabalho_id': unit_id
        }
        header = {
            'authorization' : token
        }
        url = u"{0}/distribuicao/finaliza".format(server)
        response = self.net.POST(server, url, post_data, header)
        if response:
            self.iface.actionNewProject().trigger()
            self.login_remote({
                'server' : server, 
                'user' : user, 
                'password' : password
            })

    def dump_data(self, data):
        with open(self.path_data, u"wb") as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    def load_data(self):
        try:
            with open(self.path_data, u"rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return False
    
    def show_message(self, tag):
        dialog = self.login_sap.dialog 
        if "new activity" == tag:
            html = u"<p>Deseja iniciar a próxima atividade?</p>"
            result = msgBox.show(
                text=html, 
                title=u"AVISO!", 
                status="question", 
                parent=dialog
            )
            return result
        elif "no activity" == tag:
            html = u'''<p>Não há nenhum trabalho cadastrado para você.</p>
                        <p>Procure seu chefe de seção.</p>'''
            msgBox.show(
                text=html, 
                title=u"AVISO!", 
                parent=dialog
            )
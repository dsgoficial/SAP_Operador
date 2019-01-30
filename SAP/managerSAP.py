# -*- coding: utf-8 -*-
from PyQt5 import QtCore
import sys, os, pickle
from .worksFrame import WorksFrame
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import network, msgBox

class ManagerSAP(QtCore.QObject):

    def __init__(self, iface=None, parent=None):
        super(ManagerSAP, self).__init__()
        self.path_data = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.pickle')
        self.frame = None
        self.iface = iface
        self.parent = parent
        if self.parent:
            self.net = network
            self.net.CONFIG['parent'] = parent

    def login(self, server, user, password):
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
                    data['token'] = token
                    data['server'] = server
                    data['user'] = self.config['user']
                    data['password'] = self.config['password']
                    self.dump_data(data)
                    return True
                else:
                    return self.init_works(server, token)
        return False

    def get_frame(self):
        self.frame = WorksFrame()
        self.frame.load(self.load_data())
        self.frame.close_works.connect(
            self.close_works
        )
        return self.frame
    
    def init_works(self, server, token):
        result = self.show_message("new activity")
        if result == 16384:
            header = {'authorization' : token}
            url = u"{0}/distribuicao/inicia".format(server)
            response = self.net.POST(server, url, header=header)
            data = response.json()
            if data['sucess']:
                data['token'] = token
                data['server'] = server
                data['user'] = self.config['user']
                data['password'] = self.config['password']
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
            pass
            #self.login(server, user, password)
            #self.iface.actionNewProject().trigger()

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
        dialog = self.config['dialog'] 
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
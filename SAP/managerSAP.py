# -*- coding: utf-8 -*-
from PyQt5 import QtCore
import sys, os, pickle
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import network, msgBox

class ManagerSAP(QtCore.QObject):

    def __init__(self, config={}):
        super(ManagerSAP, self).__init__()
        self.path_data = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.pickle')
        if config:
            self.config = config
            self.net = network
            self.net.CONFIG['interface'] = self.config['dialog']

    def login(self):
        post_data = {
            u"usuario" : self.config['user'],
            u"senha" : self.config['password']
        }
        server = self.config['server']
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
                    data['user'] = self.config['user']
                    data['password'] = self.config['password']
                    self.dump_data(data)
                    return True
                else:
                    return self.init_activity(server, token)
        return False
    
    def init_activity(self, server, token):
        result = self.show_message("new activity")
        if result == 16384:
            header = {'authorization' : token}
            url = u"{0}/distribuicao/inicia".format(server)
            response = self.net.POST(server, url, header=header)
            data = response.json()
            if data['sucess']:
                data['token'] = token
                data['user'] = self.config['user']
                data['password'] = self.config['password']
                self.dump_data(data)
                return True
            self.show_message("no activity")
            return False

    def close_activity(self):
        pass

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
        interface = self.config['interface']
        if "new activity" == tag:
            html = u"<p>Deseja iniciar a próxima atividade?</p>"
            result = msgBox.show(text=html, title=u"AVISO!", status="question", parent=interface)
            return result
        elif "no activity" == tag:
            html = u"<p>Não há nenhum trabalho cadastrado para você.</p><p>Procure seu chefe de seção.</p>"
            msgBox.show(text=html, title=u"AVISO!", status="question", parent=interface)
# -*- coding: utf-8 -*-
from PyQt5 import QtCore
import sys, os, pickle
from qgis import core, gui
from .worksFrame import WorksFrame
from .Login.login import Login
from Ferramentas_Producao.utils import msgBox, managerFile
from Ferramentas_Producao.utils.network import Network
from Ferramentas_Producao.utils.managerQgis import ManagerQgis
from qgis.utils import plugins
from configparser import ConfigParser

class ManagerSAP(QtCore.QObject):

    show_tools = QtCore.pyqtSignal(bool)
    close_tools = QtCore.pyqtSignal()
    close_work = QtCore.pyqtSignal()

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
        self.net = Network(self.login_sap.dialog)

    def add_action_qgis(self, b):
        if b:
            self.login_sap.action.add_on_qgis()
        else:
            self.login_sap.action.remove_from_qgis()

    def get_plugins_versions(self):
        plugins_versions = []
        for name, plugin in plugins.items():
            try:
                metadata_path = os.path.join(
                    plugin.plugin_dir,
                    'metadata.txt'
                )
                
                with open(metadata_path) as mf:
                    cp = ConfigParser()
                    cp.readfp(mf)
                    plugins_versions.append(
                        {
                            'nome' : name,
                            'versao' : cp.get('general', 'version').split('-')[0]
                        }
                    )
            except:
                pass
        return plugins_versions

    def enable_action_qgis(self, b):
        self.login_sap.action.setEnabled(b)

    def load_sap_activity_from_data(self, data):
        self.dump_data(data)
        self.show_tools.emit(True)
        
    def login(self, server, user, password):
        sucess = False
        qgis_version = core.QgsExpressionContextUtils.globalScope().variable('qgis_version').split('-')[0]
        post_data = {
            "usuario" : user,
            "senha" : password,
            'plugins' : self.get_plugins_versions(),
            'qgis' : qgis_version
        }
        url = u"{0}/login".format(server)
        response = self.net.POST(server, url, post_data)
        if response and response.json()['sucess']:
            if not( 'version' in response.json()['dados'] and int(response.json()['dados']['version']) == 2):
                self.show_message('erro version')
                return
            token = response.json()['dados']['token']
            data = self.get_current_works(server, user, password, token)
            if data and "dados" in data:
                self.update_sap_data(
                    data, 
                    server, 
                    user, 
                    password, 
                    token
                )
                sucess = True
            elif data:
                sucess = self.init_works(server, user, password, token)
        if sucess:
            self.login_sap.dialog.accept()
            self.show_tools.emit(True)
        else:
            self.close_tools.emit()
            self.login_sap.dialog.show_()

    def getWork(self, server, user, password):
        sucess = False
        qgis_version = core.QgsExpressionContextUtils.globalScope().variable('qgis_version').split('-')[0]
        post_data = {
            "usuario" : user,
            "senha" : password,
            'plugins' : self.get_plugins_versions(),
            'qgis' : qgis_version
        }
        url = u"{0}/login".format(server)
        response = self.net.POST(server, url, post_data)
        if response and response.json()['sucess']:
            if not( 'version' in response.json()['dados'] and int(response.json()['dados']['version']) == 2):
                self.show_message('erro version')
                return
            token = response.json()['dados']['token']
            return self.get_current_works(server, user, password, token)
            
    def get_frame(self):
        self.frame = WorksFrame(self.iface, self)
        self.frame.close_works.connect(
            self.close_works
        )
        self.frame.report_bug.connect(
            self.report_work_bug
        )
        return self.frame

    def update_sap_data(self, data, server, user, password, token):
        data['token'] = token
        data['server'] = server
        data['user'] = user
        data['password'] = password
        works = data['dados']['atividade']['nome']
        ManagerQgis(self.iface).save_project_var(
            'works', 
            works
        )
        ManagerQgis(self.iface).save_project_var(
            'token', 
            token
        )
        self.dump_data(data)

    def get_current_works(self, server, user, password, token):
        header = {'authorization' : token}
        url = u"{0}/distribuicao/verifica".format(server)
        response = self.net.GET(server, url, header)
        if response:
            data = response.json()
            return data
        return {}

    def init_works(self, server, user, password, token):
        result = self.show_message("new activity")
        if result == 16384:
            header = {'authorization' : token}
            url = u"{0}/distribuicao/inicia".format(server)
            response = self.net.POST(server, url, header=header)
            if response:
                data = response.json()
                if data['sucess'] and 'dados' in data:
                    self.update_sap_data(
                        data, 
                        server, 
                        user, 
                        password, 
                        token
                    )
                    return True
            self.show_message("no activity")
            return False

    def close_works(self):
        sap_data = self.load_data()
        server = sap_data['server']
        token = sap_data['token']
        activity_id = sap_data['dados']['atividade']['id']
        post_data = {
            'atividade_id' : activity_id,
            'sem_correcao' : False,
        }
        header = { 
            'authorization' : token
        }
        url = u"{0}/distribuicao/finaliza".format(server)
        response = self.net.POST(server, url, post_data, header)
        if response:
            user = sap_data['user']
            password = sap_data['password']
            self.next_work(server, user, password)

    def next_work(self, server, user, password):
        self.close_work.emit()
        self.iface.actionNewProject().trigger()
        self.login(server, user, password)

    def dump_data(self, data):
        #print(data)
        managerFile.dump_data(self.path_data, data)

    def load_data(self):
        return managerFile.load_data(self.path_data)
    
    def get_report_data(self):
        sap_data = self.load_data()
        token = sap_data['token']
        server = sap_data['server']
        header = {'authorization' : token}
        url = u"{0}/distribuicao/tipo_problema".format(server)
        response = self.net.GET(server, url, header)
        return response.json()
    
    def report_work_bug(self, report_input):
        sap_data = self.load_data()
        post_data = {
            "atividade_id" : sap_data['dados']['atividade']['id'],
        }
        post_data.update(report_input)
        sap_data = self.load_data()
        token = sap_data['token']
        server = sap_data['server']
        header = {'authorization' : token}
        url = u"{0}/distribuicao/problema_atividade".format(server)
        response = self.net.POST(server, url, post_data, header)
        if response:
            user = sap_data['user']
            password = sap_data['password']
            self.next_work(server, user, password)
    
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
        elif "erro version" == tag:
            html = u'''<p>Versão do 'SAP' incorreta!</p>'''
            msgBox.show(
                text=html, 
                title=u"AVISO!", 
                parent=dialog
            )
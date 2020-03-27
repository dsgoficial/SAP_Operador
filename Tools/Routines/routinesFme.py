#! -*- coding: utf-8 -*-
from qgis import core, gui
from PyQt5 import QtCore
from .statusRoutine import StatusRoutine
import re, sys, os, json
from Ferramentas_Producao.Database.postgresql import Postgresql
from Ferramentas_Producao.SAP.managerSAP import ManagerSAP
from Ferramentas_Producao.utils import msgBox
from Ferramentas_Producao.utils.network import Network
from Ferramentas_Producao.utils.managerQgis import ManagerQgis

class RoutinesFme(QtCore.QObject):

    message = QtCore.pyqtSignal(str)

    def __init__(self, iface, parent=None):
        super(RoutinesFme, self).__init__()
        self.iface = iface 
        self.sap_mode = False
        self.parent = parent
        self.net = Network(self.parent)
        self.is_running = False
    
    def get_server(self):
        m_qgis = ManagerQgis(self.iface)
        return m_qgis.load_qsettings_var('FME/server')

    def save_server(self, server):
        m_qgis = ManagerQgis(self.iface)
        m_qgis.save_qsettings_var('FME/server', server)

    def get_routines_data(self, server=''):
        fme_routines = []
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            if  'fme' in sap_data and sap_data['fme']:
                
                for rout_data in sap_data['fme']:
                    server = u"http://{0}:{1}/api".format( rout_data['servidor'], rout_data['porta'] )
                    cat = u"&workspace={0}".format( rout_data['rotina'] )
                    url = u"{0}/versions?last=true{1}".format( server, cat )
                    response = self.net.GET(server, url)
                    if response:
                        routines = response.json()['data']
                        for r in routines:
                            r['description'] = r['workspace_description']
                            r['type_routine'] = 'fme'
                        fme_routines.append(r)
        else:
            if server:
                url = u"{0}/versions?last=true".format( server )
                response = self.net.GET(server, url)
                if response:
                    routines = response.json()['data']
                    for r in routines:
                        r['description'] = r['workspace_description']
                        r['type_routine'] = 'fme'
                        fme_routines.append(r)
        self.save_server( server )
        return fme_routines

    def get_db_connection_data(self):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()
            db_connection = sap_data['dados']['atividade']['banco_dados']
            db_name = db_connection['nome']
            db_host = db_connection['servidor']
            db_port = db_connection['porta']
        else:
            postgresql = Postgresql()
            db_connection = postgresql.get_connection_config()
            db_name = db_connection['db_name']
            db_host = db_connection['db_host']
            db_port = db_connection['db_port']
        db_connection_data = {
            'db_name' : db_name,
            'db_port' : db_port,
            'db_host' : db_host
        }
        return db_connection_data

    def get_workspace_geometry(self, settings_user):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            geometry = "'{0}'".format(sap_data["geom"])
        else:
            workspace_name = settings_user['workspace_name']
            postgresql = Postgresql()
            frames_wkt = postgresql.get_frames_wkt()
            if not(workspace_name == u"Todas"):
                wkt = frames_wkt[workspace_name]
                geometry = "'{0}'".format(wkt)
            return False
        return geometry

    def run(self, routine_data):
        html = ''
        self.routine_data = routine_data
        settings_user = ManagerQgis(self.iface).load_project_var('settings_user')
        if not settings_user :
            self.message.emit(u"<p>Não há dados carregados nesse projeto!</p>")
            return
        geometry = self.get_workspace_geometry(settings_user)
        if not geometry:
            self.message.emit(u"<p>Carregue uma unidade de trabalho para executar essa rotina.</p>")
            return
        db_connection_data = self.get_db_connection_data()
        post_json  = self.get_post_data(self.routine_data, geometry, db_connection_data)
        routine_id =  self.routine_data['id']
        post_data = { 'parameters' : post_json}
        server  = self.get_server()
        url = '{0}/versions/{1}/jobs'.format(
            server, 
            routine_id
        )
        response = self.net.POST(server, url, post_data)
        if not response:
            self.message.emit(u"<p>Erro ao iniciar rotina.</p>")
            return
        url_get_status = '{0}/jobs/{1}'.format(
            server, 
            response.json()['data']['job_uuid']
        )
        self.running = True
        self.worker = StatusRoutine(url_get_status, server)
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.worker.finish.connect(self.stop)
        self.thread.started.connect(
            self.worker.run
        )
        self.thread.start()

    def stop(self, response_routine):
        if self.worker:
            self.worker.deleteLater()
            self.thread.quit()
            self.thread.deleteLater()
            self.thread = self.worker = self.running = False
            log_html = self.format_log(response_routine)
            self.message.emit(log_html)
               
    def get_post_data(self, routine_data, geometry, db_connection):
        post_data = {}
        for parameter in routine_data['parameters']:
            if 'dbarea' in parameter:
                post_data[parameter] = geometry
            elif 'dbname' in parameter:
                post_data[parameter] = db_connection['db_name']
            elif 'dbport' in parameter:
                post_data[parameter] = db_connection['db_port']
            elif 'dbhost' in parameter:
                post_data[parameter] = db_connection['db_host']
            else:
                post_data[parameter] = ''
        return post_data
    
    def format_log(self, response_routine):
        status = response_routine[u'status']
        routine_name = self.routine_data['workspace_name']
        output = u"<p>[rotina nome] : {0}</p>".format(routine_name)
        for flags in response_routine['log'].split('|'):
            row = u"""<p>[rotina flags] : {0}</p>""".format(flags)
            output += row
        return output
    
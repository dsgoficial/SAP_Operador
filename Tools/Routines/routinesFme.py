#! -*- coding: utf-8 -*-
from qgis import core, gui
from PyQt5 import QtCore
from .statusRoutine import StatusRoutine
import re, sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from Database.postgresql import Postgresql
from SAP.managerSAP import ManagerSAP
from utils import network, msgBox
from utils.managerQgis import ManagerQgis

class RoutinesFme(QtCore.QObject):

    message = QtCore.pyqtSignal(str)

    def __init__(self, iface, parent=None):
        super(RoutinesFme, self).__init__()
        self.iface = iface 
        self.sap_mode = False
        self.parent = parent
        self.net = network
        self.net.CONFIG['parent'] = self.parent
        self.is_running = False

    def get_routines_data(self, server=''):
        data = {}
        server = self.get_server(server)
        if server:
            cat = ''
            if self.sap_mode:
                sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
                if  sap_data['fme']:
                    cat = sap_data['fme']['categoria']
                    cat = u"&category={0}".format(cat)
            url = u"{0}/versions?last=true{1}".format(
                server,
                cat
            )
            response = self.net.GET(server, url)
            if response:
                data = response.json()['data']
                for r in data:
                    r['description'] = r['workspace_description']
                    r['type_routine'] = 'fme'
        return data

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

    def get_server(self, server=''):
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            if  sap_data['fme'] and sap_data['fme']['servidor']:
                server = sap_data['fme']['servidor']
                server = u"http://{0}".format(server)
        else:
            m_qgis = ManagerQgis(self.iface)
            if server:
                m_qgis.save_qsettings_var('FME/server', server)
            else:
                server = m_qgis.load_qsettings_var('FME/server')
        return server

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
        if settings_user :
            geometry = self.get_workspace_geometry(settings_user)
            if geometry:
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
            else:
                html = u"<p>Carregue uma unidade de trabalho para executar essa rotina.</p>"
        else:
            html = u"<p>Não há dados carregados nesse projeto!</p>"
        if html:
            self.message.emit(html)

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
    
#! -*- coding: utf-8 -*-
from qgis import core, gui
from PyQt5 import QtCore
import re, sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from Database.postgresql import Postgresql
from SAP.managerSAP import ManagerSAP
from utils import msgBox

class RoutinesFme(QtCore.QObject):

    def __init__(self, iface, routine_data):
        super(RoutinesFme, self).__init__()
        self.iface = iface 
        self.sap_mode = False
        self.routine_data = routine_data
        self.init_postgresql()

    def init_postgresql(self):
        self.postgres = Postgresql()
        if self.sap_mode:
            sap_data = ManagerSAP().load_data()
            db_data = sap_data['dados']['atividade']['banco_dados']
            db_name = db_data['nome']
            self.postgresql.set_connections_data({
                'db_name' : db_name,
                'db_host' : db_data['servidor'],
                'db_port' : db_data['porta'],
                'db_user' : sap_data['user'],
                'db_password' : sap_data['password'] 
            })
        else:
            pass


    
    def run(self):
        pg_con = self.tool_interface.loadPostgresDatabase()
        workspace = self.tool_interface.getWorkspace()
        loginData = self.tool_interface.data
        
        geomUnit = "'{0}'".format(
            loginData["dados"]["atividade"]["geom"] if loginData else pg_con.dbJson['workspaces'][workspace]
        ) 
        postJson  = self.get_post_data(self.rotine_data, geomUnit, pg_con.dbJson['dataConnection'])
        rotineId =  self.rotine_data['id']
        postData = { 'parameters' : postJson}
        url = 'http://{0}/versions/{1}/jobs'.format(
            self.server, 
            rotineId
        )
        response = Network().POST(self.server, url, postData)
        url_to_status = 'http://{0}/jobs/{1}'.format(
            self.server, 
            response.json()['data']['job_uuid']
        )
        self.active_routine = True
        self.worker = Status_rotine(url_to_status, self.server)
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.worker.finish.connect(self.stop_rotine_fme)
        self.thread.started.connect(
            self.worker.run
        )
        self.thread.start()
    
    #
    def msg_erro(self, msg):
        QtGui.QMessageBox.critical(
            self.iface.mainWindow(),
            u"Erro:", 
            msg
        )            
            
    def get_post_data(self, rotine_data, geomUnit, db_data):
        postData = {}
        for parameter in rotine_data['parameters']:
            if 'dbarea' in parameter:
                postData[parameter] = geomUnit
            elif 'dbname' in parameter:
                postData[parameter] = db_data['dbname']
            elif 'dbport' in parameter:
                postData[parameter] = db_data['port']
            elif 'dbhost' in parameter:
                postData[parameter] = db_data['host']
            else:
                postData[parameter] = ''
        return postData

    def result_msg(self, text):
        QtGui.QMessageBox.information(
            self.iface.mainWindow(),
            u"Resultado:", 
            text
        )

    def stop_rotine_fme(self, response_rotine):
        if self.worker:
            self.worker.deleteLater()
            self.thread.quit()
            self.thread.deleteLater()
            self.thread = self.worker = self.active_routine = False
            log_html = self.format_log(response_rotine)
            self.result_msg(log_html)
    
    def format_log(self, response_rotine):
        status = response_rotine[u'status']
        rotine_name = self.rotine_data['workspace_name']
        output = u"<p>[rotina nome] : {0}</p>".format(rotine_name)
        for flags in response_rotine['log'].split('|'):
            row = u"""<p>[rotina flags] : {0}</p>""".format(flags)
            output += row
        return output
    
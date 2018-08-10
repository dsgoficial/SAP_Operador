# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from managerNetwork.network import Network
from custom_thread.status_rotine import Status_rotine
from rotines_local import Rotines_Local

class Rotines_Manager(QtCore.QObject):

    stop_progressbar = QtCore.pyqtSignal()

    def __init__(self, iface, tool_interface):
        super(Rotines_Manager, self).__init__()
        self.tool_interface = tool_interface
        self.iface = iface
        self.thread = self.worker = self.isActiveRotine = self.server = False 

    def msg_erro(self, msg):
        QtGui.QMessageBox.critical(
            self.iface.mainWindow(),
            u"Erro:", 
            msg
        )

    def get_server_fme(self):
        if self.tool_interface.data and self.tool_interface.data['dados']['atividade']['fme']:
            self.server = self.tool_interface.data['dados']['atividade']['fme']['servidor']
            cat = self.tool_interface.data['dados']['atividade']['fme']['categoria']
        else:
            self.server = self.tool_interface.serverFMELineEdit.text()
        if self.server:
            url = u"http://{0}/versions?last=true".format(self.server)
            if cat:
                url += u"&category={0}".format(cat)     
            return url 
        return False

    def getRotinesFme(self):
        url = self.get_server_fme()
        if url:
            server_response = Network().GET(self.server, url)
            if server_response == 1:
                self.msg_erro(u"IP do servidor incorreto!")
                return False
            elif server_response == 2:
                self.msg_erro(u"Conexão recusada!")
                return False
            data = server_response.json()
            return data
        return False
            
    def startRotine(self, rotine_data):
        self.rotine_data = rotine_data
        if rotine_data['type_rotine'] == 'fme':
            self.start_rotine_fme()
        elif rotine_data['type_rotine'] == 'local':
            self.start_rotine_local()

    def start_rotine_local(self):
        self.r_local = Rotines_Local(self.iface, self.rotine_data, self.tool_interface)
        self.r_local.finish.connect(self.result_msg)
        self.r_local.run()    

    def start_rotine_fme(self):
        if not(self.isActiveRotine):
            self.tool_interface.rotinesProgressBar.setRange(0,0)
            pg_con = self.tool_interface.getPostgresConnection()
            workspace = self.tool_interface.getWorkspace()
            loginData = self.tool_interface.data
            geomUnit = (
                "'{0}'".format(loginData["dados"]["atividade"]["geom"]) if loginData else pg_con.dbJson['workspaces'][workspace] 
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
            self.isActiveRotine = True
            self.worker = Status_rotine(url_to_status, self.server)
            self.thread = QtCore.QThread()
            self.worker.moveToThread(self.thread)
            self.worker.finish.connect(self.stop_rotine_fme)
            self.thread.started.connect(
                self.worker.run
            )
            self.thread.start()
            
    def get_post_data(self, rotine_data, geomUnit, db_data):
        postData = {}
        for parameter in rotine_data['parameters']:
            if 'dbarea_' in parameter:
                postData[parameter] = geomUnit
            elif 'dbname_' in parameter:
                postData[parameter] = db_data['dbname']
            elif 'dbport_' in parameter:
                postData[parameter] = db_data['port']
            elif 'dbhost_' in parameter:
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
            self.thread = self.worker = self.isActiveRotine = False
            log_html = self.format_log(response_rotine)
            self.result_msg(log_html)
        self.tool_interface.rotinesProgressBar.setRange(0, 1)  
    
    def format_log(self, response_rotine):
        status = response_rotine[u'status']
        rotine_name = self.rotine_data['workspace_name']
        output = u"<p>[rotina nome] : {0}</p>".format(rotine_name)
        for flags in response_rotine['log'].split('|'):
            row = u"""<p>[rotina flags] : {0}</p>""".format(flags)
            output += row
        return output
    
        
    
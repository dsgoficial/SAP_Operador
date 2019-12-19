import os, sys, time, requests, json
from PyQt5 import QtCore
from qgis import core, gui
from Ferramentas_Producao.utils.network import Network
from Ferramentas_Producao.SAP.managerSAP import ManagerSAP

class Canvas(QtCore.QThread):

    def __init__(self, parent=None):
        super(Canvas, self).__init__(parent)
        self.running = True
        self.sendMessage = False

    def on_source(self, server, token, activityId):
        self.server = server
        self.token = token
        self.activityId = activityId

    def run(self):
        while self.running:
            if self.sendMessage:
                header = { 
                    'authorization' : self.token,
                    'content-type' : 'application/json'
                }
                url = "{0}/microcontrole/acao".format(self.server) 
                postData = {
                    "atividade_id": int(self.activityId)
                }
                session = requests.Session()
                session.trust_env = False
                session.post(url, data=json.dumps(postData), headers=header)
                self.sendMessage = False
            time.sleep(60)

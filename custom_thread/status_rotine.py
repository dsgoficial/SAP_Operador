from PyQt4 import QtCore, QtGui
from time import sleep
import json
import requests
import os
    
class Status_rotine(QtCore.QObject):

    finish = QtCore.pyqtSignal(dict)
    
    def __init__(self, url, server, parent=None):
        super(Status_rotine, self).__init__(parent)
        self.url = url
        self.server = server
     
    def getStatus(self):
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.get(self.url)
            return response.json()['data'] #['status'] 1 -- rodando, 2 -- executado, 3 -- erro
        except:
            data = {'status': 'erro', 'log':'Erro no plugin!'}
            return data 
    
    def run(self):        
        for p in range(150):
            sleep(3)
            data = self.getStatus()
            if data['status'] in [2, 3, "erro"]:
                break
        self.finish.emit(data)
        
                  
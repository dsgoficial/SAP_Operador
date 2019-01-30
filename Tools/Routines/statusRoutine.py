from PyQt5 import QtCore
from time import sleep
import requests
    
class StatusRoutine(QtCore.QObject):

    finish = QtCore.pyqtSignal(dict)
    
    def __init__(self, url_get_status, server, parent=None):
        super(StatusRoutine, self).__init__(parent)
        self.url_get_status = url_get_status
        self.server = server
     
    def get_status(self):
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.get(self.url_get_status)
            session.close()
            return response.json()['data'] #['status'] 1 -- rodando, 2 -- executado, 3 -- erro
        except:
            data = {'status': 'erro', 'log':'Erro no plugin!'}
            return data 
    
    def run(self):        
        for p in range(150):
            sleep(3)
            data = self.get_status()
            if data['status'] in [2, 3, "erro"]:
                break
        self.finish.emit(data)
        
                  
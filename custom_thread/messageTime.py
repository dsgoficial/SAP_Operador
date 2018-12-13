from PyQt4 import QtCore, QtGui
from time import sleep
import json
import requests
import os

RUNNING = 1

class MessageTime(QtCore.QObject):

    finish = QtCore.pyqtSignal()
    
    def __init__(self, time, parent=None):
        super(MessageTime, self).__init__(parent)
        self.time = time

    def run(self):        
        while RUNNING:
            sleep(self.time)
            self.finish.emit()
       
        
                  
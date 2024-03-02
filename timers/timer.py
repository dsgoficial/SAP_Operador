from SAP_Operador.interfaces.ITimer import ITimer
from PyQt5 import QtCore, QtWidgets, QtGui 

class Timer(ITimer):

    def __init__(self):
        super(Timer, self).__init__()
        self.time = QtCore.QTimer()
        self.time.timeout.connect(self.triggerCallbacks)
        self.callbacks = []
        self.seconds = None

    def addCallback(self, callback):
        self.callbacks.append(callback)
    
    def removeCallback(self, callback):
        self.callbacks = list(filter(lambda a: a != callback, self.callbacks))

    def triggerCallbacks(self):
        [ cb() for cb in self.callbacks ]

    def start(self, seconds):
        self.seconds = seconds
        self.time.start(self.seconds)

    def reset(self):
        self.stop()
        self.time.start(self.seconds)

    def stop(self):
        self.time.stop()
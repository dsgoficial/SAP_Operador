# -*- coding: utf-8 -*-

import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from qgis.utils import iface
from Ferramentas_Producao.Microcontroller.Monitor.canvas import Canvas
from Ferramentas_Producao.SAP.managerSAP import ManagerSAP

class Monitoring(QtCore.QObject):
    
    sendCanvasInfo = QtCore.pyqtSignal(str, str, int)

    def __init__(self, iface):
        super(Monitoring, self).__init__()
        self.iface = iface
        self.canvas = None

    def startCanvasEventsQgis(self):
        iface.mapCanvas().mapCanvasRefreshed.connect(
            self.updateCanvasStatus
        )

    def stopCanvasEventsQgis(self):
        try:
            iface.mapCanvas().mapCanvasRefreshed.disconnect(
                self.updateCanvasStatus
            )
        except:
            pass

    def updateCanvasStatus(self):
        if self.canvas:
            self.canvas.sendMessage = True

    def startCanvas(self):
        self.stopCanvas()
        self.canvas = Canvas()
        sap_data = ManagerSAP(self.iface).load_data()
        server = sap_data['server']
        token = sap_data['token']
        activityId = int(sap_data['dados']['atividade']['id'])
        self.sendCanvasInfo.connect(self.canvas.on_source)
        self.sendCanvasInfo.emit(server, token, activityId)
        self.canvas.start()
        self.startCanvasEventsQgis()

    def stopCanvas(self):
        try:
            self.canvas.running = False
        except:
            pass
        try:
            self.stopCanvasEventsQgis()
        except:
            pass

# -*- coding: utf-8 -*-

import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from Ferramentas_Producao.utils.network import Network
from Ferramentas_Producao.SAP.managerSAP import ManagerSAP

class Canvas(QtCore.QObject):
    def __init__(self, iface):
        self.iface = iface
        self.network = Network()
        self.time = QtCore.QTimer()
        self.is_active_canvas = False
        self.seconds = 1000 * 60

    def connect_signals(self):
        self.time.timeout.connect(
            lambda: self.send_info()
        )
        self.iface.mapCanvas().mapCanvasRefreshed.connect(
            lambda: self.set_active_canvas()
        )

    def disconnect_signals(self):
        try:
            self.time.timeout.disconnect(
                lambda: self.send_info()
            )
        except:
            pass
        try:
            self.iface.mapCanvas().mapCanvasRefreshed.disconnect(
                self.set_active_canvas
            )
        except:
            pass

    def start(self):
        self.disconnect_signals()
        self.connect_signals()
        self.time.stop()        
        self.time.start(self.seconds)

    def stop(self):
        self.disconnect_signals()
        self.time.stop()

    def set_active_canvas(self):
        self.is_active_canvas = True
        
    def send_info(self):
        if not self.is_active_canvas:
            return
        sap_data = ManagerSAP(self.iface).load_data()
        host = sap_data['server']
        token = sap_data['token']
        activity_id = int(sap_data['dados']['atividade']['id'])
        header = { 
            'authorization' : token
        }
        url = "{0}/microcontrole/acao".format(host) 
        postdata = {
            "atividade_id": int(activity_id)
        }
        self.network.POST(host, url, postdata, header=header)
        self.is_active_canvas = False
     
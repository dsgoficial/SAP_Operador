# -*- coding: utf-8 -*-

import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from Ferramentas_Producao.Microcontroller.Monitor.canvas import Canvas

class Monitoring(QtCore.QObject):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = Canvas(self.iface)
        self.monitors = [
            self.canvas
        ]

    def start(self):
        for m in self.monitors:
            m.start()

    def stop(self):
        for m in self.monitors:
            m.stop()

# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui, utils

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))

class Track(QtCore.QObject):

    layerModified = QtCore.pyqtSignal()

    def __init__(self, iface, dataLogin=False):
        super(Track, self).__init__()
        self.dataLogin = dataLogin
        self.iface = iface
        self.track_list = self.iface.legendInterface().layers()
        self.connect_track_layers()
        self.start_update_track_list()

    def start_update_track_list(self):
        self.iface.mapCanvas().layersChanged.connect(self.update_track_list)
    
    def update_track_list(self):
        self.disconnect_track_layer()
        self.track_list = self.iface.legendInterface().layers()
        self.connect_track_layers()

    def disconnect_track_layer(self):
        for layer in self.track_list:
            try:
                layer.layerModified.disconnect(self.layer_modified) 
            except:
                pass

    def connect_track_layers(self):
        for layer in self.track_list:
            layer.layerModified.connect(self.layer_modified) 

    def layer_modified(self):
        self.layerModified.emit()
import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from .Operations.addFeatures import AddFeatures
from .Operations.changedGeometry import ChangedGeometry

class ValidateOperations(QtCore.QObject):
    def __init__(self, iface):
        super(ValidateOperations, self).__init__()
        self.iface = iface
        self.track_list = []
        self.addFeatures = None
        self.changedGeometry = None

    def start(self):
        self.init_operations()
        self.update_track_list()
    
    def stop(self):
        self.disconnect_layers()
        self.finish_operations()

    def update_track_list(self):
        self.disconnect_layers()
        self.track_list = [
            l for l in self.iface.mapCanvas().layers()
            if l.type() == core.QgsMapLayer.VectorLayer
        ]
        self.connect_layers()
    
    def init_operations(self):
        self.addFeatures = AddFeatures(self.iface)
        self.changedGeometry = ChangedGeometry(self.iface)

    def finish_operations(self):
        del self.addFeatures
        del self.changedGeometry

    def check_operations(self):
        self.addFeatures.validate()
        self.changedGeometry.validate()

    def disconnect_layers(self):
        for lyr in self.track_list:
            try:
                lyr.layerModified.disconnect(
                    self.check_operations
                )
            except:
                pass
    
    def connect_layers(self):
        for lyr in self.track_list:
            lyr.layerModified.connect(
                self.check_operations
            )
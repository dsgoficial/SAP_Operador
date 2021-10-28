import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from Ferramentas_Producao.factories.spatialOperationFactory import SpatialOperationFactory

class ValidateUserOperations(QtCore.QObject):
    
    def __init__(
            self, 
            qgis,
            spatialOperationFactory=SpatialOperationFactory()
        ):
        super(ValidateUserOperations, self).__init__()
        self.qgis = qgis
        self.spatialOperationFactory = spatialOperationFactory
        self.trackList = []
        self.addFeatures = None
        self.changedGeometry = None
        self.traceableLayerIds = []
        self.ewkt = ''

    def setTraceableLayerIds(self, traceableLayerIds):
        self.traceableLayerIds = traceableLayerIds

    def getTraceableLayerIds(self):
        return self.traceableLayerIds

    def setWorkspaceWkt(self, ewkt):
        self.ewkt = ewkt

    def getWorkspaceWkt(self):
        return self.ewkt

    def start(self):
        self.stop()
        self.initOperations()
        self.updateTrackList()

    def initOperations(self):
        self.addFeatures = self.spatialOperationFactory.createOperation( 'AddFeatures', self.qgis, self.getWorkspaceWkt() )
        self.changedGeometry = self.spatialOperationFactory.createOperation( 'ChangedGeometry', self.qgis, self.getWorkspaceWkt() )

    def updateTrackList(self):
        traceableLayerIds = self.getTraceableLayerIds()
        self.disconnectLayers()
        self.trackList = [
            l for l in self.qgis.getLoadedVectorLayers()
            if (
                l.type() == core.QgsMapLayer.VectorLayer
                and
                l.id() in traceableLayerIds
            )
        ]
        self.connectLayers()

    def connectLayers(self):
        for lyr in self.trackList:
            lyr.layerModified.connect(
                self.checkOperations
            )
    
    def disconnectLayers(self):
        for lyr in self.trackList:
            try:
                lyr.layerModified.disconnect(
                    self.checkOperations
                )
            except:
                pass

    def checkOperations(self):
        self.addFeatures.validate()
        self.changedGeometry.validate()
    
    def stop(self):
        self.disconnectLayers()
        self.finishOperations()

    def finishOperations(self):
        del self.addFeatures
        del self.changedGeometry

    
    
    
# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui, utils

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))

class Summary(QtCore.QObject):

    def __init__(self, iface, dataLogin):
        super(Summary, self).__init__()
        self.dataLogin = dataLogin
        self.iface = iface
        self.changes = {}
        self.start()

    def start(self):
        core.QgsProject.instance().layerTreeRoot().addedChildren.connect(self.track)

    def getLayerByName(self, name):
        dbname = 'rs_rf1'
        result = core.QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in result:
            uriClass = core.QgsDataSourceURI(layer.styleURI())
            test = (
                (dbname == layer.source().split(' ')[0][8:-1]) and
                (name == uriClass.table())
            )
            if test:
                self.iface.setActiveLayer(layer)
                return layer
        return False

    def track(self, rTree):
        track_lyrs = ["constr_edificacao_a"]
        current_layer = self.iface.activeLayer()
        for lyrT in rTree.findLayers():
            name = lyrT.name()
            if name in track_lyrs:
                vector_lyr = self.getLayerByName(name)
                if vector_lyr:
                    self.iface.setActiveLayer(vector_lyr)
                    committedFeaturesRemoved 
                    committedGeometriesChanges 
                    committedFeaturesAdded 
                    
    
    def count_points(self, geom):
        if geom.type() == 2:#polygon
            count = 0
            if geom.isMultipart():
                parts = geom.asMultiPolygon()
            else:
                parts = [ geom.asPolygon() ]
            for part in parts:
                for ring in part:
                    count += len(ring) - 1
            return count 
        elif geom.type() == 1:#line
            count = 0
            if geom.isMultipart():
                parts = geom.asMultiPolyline()
            else:
                parts = [ geom.asPolyline() ]
            for part in parts:
                count += len(part)
            return count
        else:
            return 1

    def features_removed(self, fid, deletedFeatureIds):
        #print fid[:15], len(deletedFeatureIds)
        pass

    def features_added(self, fid, addedFeatures):
        #print fid[:15], addedFeatures[0].id() , self.count_points(addedFeatures[0].geometry()), addedFeatures[0].geometry().length()
        pass

    def features_geom_changes(self, fid, changedGeometries):
        #print fid, len(changedGeometries.keys())
        pass

    
        
    def summary_changes(self):
        pass

    '''
        committedFeaturesRemoved (id, geom_removed)
        committedGeometriesChanges (id, geom_changed)
        committedFeaturesAdded (id, geom_added)
        '''
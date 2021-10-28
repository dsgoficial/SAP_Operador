# -*- coding: utf-8 -*-

import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from .operation import Operation

class AddFeatures( Operation ):

    def __init__(self, qgis, workspaceWkt):
        super(AddFeatures, self).__init__(qgis=qgis, workspaceWkt=workspaceWkt)

    def validate(self):
        activeVectorLayer = self.qgis.getActiveVectorLayer()
        if not activeVectorLayer:
            return
        featuresAdded = activeVectorLayer.editBuffer().addedFeatures() if activeVectorLayer.editBuffer() else ''
        self.checkAddFeature( featuresAdded ) if featuresAdded else ''

    def checkAddFeature(self, featuresAdded):
        activeVectorLayer = self.qgis.getActiveVectorLayer()
        workspaceGeometry = self.getWorkspaceGeometry()
        if not workspaceGeometry:
            return
        featsKeys = sorted( list( featuresAdded.keys() ) )[:2]
        erro = False
        for i, fk in enumerate( featsKeys ):
            feat = featuresAdded[ fk ]
            validGeom = workspaceGeometry.intersects( feat.geometry() ) == False
            if validGeom and i == 0:
                activeVectorLayer.deleteFeature(fk)
                erro = True
            elif validGeom:
                activeVectorLayer.undoStack().undo()
                erro = True
        if not erro:
            return
        message = '''<p style="color:red">
            A aquisição da camada "{}" está fora da moldura!
        </p>'''.format( activeVectorLayer.name() )
        self.showErrorMessageBox( self.qgis.getMainWindow(), title="Erro", message=message)
        self.qgis.canvasRefresh()

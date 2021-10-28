# -*- coding: utf-8 -*-

import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from .operation import Operation

class ChangedGeometry( Operation ):
    
    def __init__(self, qgis, workspaceWkt):
        super(ChangedGeometry, self).__init__(qgis=qgis, workspaceWkt=workspaceWkt)

    def validate(self):
        activeVectorLayer = self.qgis.getActiveVectorLayer()
        if not activeVectorLayer:
            return
        changedGeometries = activeVectorLayer.editBuffer().changedGeometries() if activeVectorLayer.editBuffer() else ''
        self.checkChangedGeometry( changedGeometries ) if changedGeometries else ''

    def checkChangedGeometry(self, changedGeometries):
        activeVectorLayer = self.qgis.getActiveVectorLayer()
        workspaceGeometry = self.getWorkspaceGeometry()
        if not workspaceGeometry:
            return
        featKey = sorted(list(changedGeometries.keys()))[0]
        featGeometry = changedGeometries[ featKey ]
        if workspaceGeometry.intersects( featGeometry ) == True:
            return
        message = '''<p style="color:red">
            A edição da camada "{}" está fora da moldura!
        </p>'''.format(activeVectorLayer.name())
        self.showErrorMessageBox( self.qgis.getMainWindow(), title="Erro", message=message)
        activeVectorLayer.undoStack().undo()
        self.qgis.canvasRefresh()

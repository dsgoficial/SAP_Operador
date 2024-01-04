import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

class Operation( QtCore.QObject ):

    def __init__(
            self,
            qgis,
            workspaceWkt=None,
            messageFactory=None,
        ):
        super(Operation, self).__init__()
        self.qgis = qgis
        self.workspaceWkt = workspaceWkt
        self.messageFactory = UtilsFactory().createMessageFactory() if messageFactory is None else messageFactory
    
    def setWorkspaceWkt(self, workspaceWkt):
        self.workspaceWkt = workspaceWkt

    def getWorkspaceWkt(self):
        return self.workspaceWkt

    def getWorkspaceGeometry(self):
        if not self.workspaceWkt:
            return
        return core.QgsGeometry.fromWkt( self.getWorkspaceWkt() )

    def showErrorMessageBox(self, parent, title, message):
        messageDlg = self.messageFactory.createMessage('ErrorMessageBox')
        messageDlg.show(parent, title, message)
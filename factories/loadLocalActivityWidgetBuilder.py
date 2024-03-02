from PyQt5 import QtWidgets, QtGui, QtCore
from SAP_Operador.widgets.loadLocalActivity import LoadLocalActivity

class LoadLocalActivityWidgetBuilder:

    def __init__(self):
        super(LoadLocalActivityWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = LoadLocalActivity()

    def setController(self, controller):
        self.obj.setController( controller )
    
    def setStyleNames(self, styleNames):
        self.obj.setStyleNames(styleNames)

    def setWorkspaceSelectItems(self, selectItems):
        self.obj.setWorkspaceSelectItems( selectItems )

    def setLayersSelectItems(self, selectItems):
        self.obj.setLayersSelectItems( selectItems )

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
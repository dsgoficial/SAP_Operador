from PyQt5 import QtWidgets, QtGui, QtCore
from SAP_Operador.interfaces.IActivityInputLinksWidgetBuilder import IActivityInputLinksWidgetBuilder
from SAP_Operador.widgets.activityInputLinks import ActivityInputLinks

class ActivityInputLinksWidgetBuilder(IActivityInputLinksWidgetBuilder):

    def __init__(self):
        super(ActivityInputLinksWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ActivityInputLinks()

    def setController(self, controller):
        self.obj.setController( controller )

    def setInputs(self, inputData):
        self.obj.setInputs( inputData )

    def adjustWidgets(self):
        self.obj.adjustWidgets()

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
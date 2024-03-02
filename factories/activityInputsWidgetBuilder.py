from PyQt5 import QtWidgets, QtGui, QtCore
from SAP_Operador.interfaces.IActivityInputsWidgetBuilder import IActivityInputsWidgetBuilder
from SAP_Operador.widgets.activityInputs import ActivityInputs

class ActivityInputsWidgetBuilder(IActivityInputsWidgetBuilder):

    def __init__(self):
        super(ActivityInputsWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ActivityInputs()

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
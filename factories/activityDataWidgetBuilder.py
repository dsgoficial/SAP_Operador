from PyQt5 import QtWidgets, QtGui, QtCore
from SAP_Operador.interfaces.IActivityDataWidgetBuilder import IActivityDataWidgetBuilder
from SAP_Operador.widgets.activityData import ActivityData

class ActivityDataWidgetBuilder(IActivityDataWidgetBuilder):

    def __init__(self):
        super(ActivityDataWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ActivityData()

    def setController(self, controller):
        self.obj.setController( controller )

    def enabledMenuButton(self, enable):
        self.obj.enabledMenuButton( enable )
    
    def enableWorkflowButton(self, enable):
        self.obj.enableWorkflowButton(enable)

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
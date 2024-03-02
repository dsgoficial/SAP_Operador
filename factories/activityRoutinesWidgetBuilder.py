from PyQt5 import QtWidgets, QtGui, QtCore
from SAP_Operador.interfaces.IActivityRoutinesWidgetBuilder import IActivityRoutinesWidgetBuilder
from SAP_Operador.widgets.activityRoutines import ActivityRoutines

class ActivityRoutinesWidgetBuilder(IActivityRoutinesWidgetBuilder):

    def __init__(self):
        super(ActivityRoutinesWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ActivityRoutines()

    def setController(self, controller):
        self.obj.setController( controller )

    def setRoutines(self, routines):
        self.obj.setRoutines( routines )

    def adjustWidgets(self):
        self.obj.adjustWidgets()

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
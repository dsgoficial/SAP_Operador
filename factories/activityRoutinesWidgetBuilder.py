from PyQt5 import QtWidgets, QtGui, QtCore
from Ferramentas_Producao.interfaces.IActivityRoutinesWidgetBuilder import IActivityRoutinesWidgetBuilder
from Ferramentas_Producao.widgets.activityRoutines import ActivityRoutines

class ActivityRoutinesWidgetBuilder(IActivityRoutinesWidgetBuilder):

    def __init__(self):
        super(ActivityRoutinesWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ActivityRoutines()

    def setMediator(self, mediator):
        self.obj.setMediator( mediator )

    def setRoutines(self, routines):
        self.obj.setRoutines( routines )

    def adjustWidgets(self):
        self.obj.adjustWidgets()

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
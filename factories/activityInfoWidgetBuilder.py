from PyQt5 import QtWidgets, QtGui, QtCore
from Ferramentas_Producao.interfaces.IActivityInfoWidgetBuilder import IActivityInfoWidgetBuilder
from Ferramentas_Producao.widgets.activityInfo import ActivityInfo

class ActivityInfoWidgetBuilder(IActivityInfoWidgetBuilder):

    def __init__(self):
        super(ActivityInfoWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ActivityInfo()

    def setController(self, controller):
        self.obj.setController( controller )

    def addObservation(self, title, description):
        self.obj.addObservation( title, description )

    def setDescription(self, title, description):
        self.obj.setDescription( title, description )
    
    def setNotes(self, title, notes):
        if not notes:
            return
        self.obj.setNotes( title, notes )

    def setRequirements(self, title, requirements):
        self.obj.setRequirements(title, requirements)

    def setButtons(self):
        self.obj.setButtons()

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
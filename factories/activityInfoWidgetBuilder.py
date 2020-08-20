from PyQt5 import QtWidgets, QtGui, QtCore
from Ferramentas_Producao.interfaces.IActivityInfoWidgetBuilder import IActivityInfoWidgetBuilder
from Ferramentas_Producao.widgets.activityInfo import ActivityInfo

class ActivityInfoWidgetBuilder(IActivityInfoWidgetBuilder):

    def __init__(self):
        super(ActivityInfoWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ActivityInfo()

    def setMediator(self, mediator):
        self.obj.setMediator( mediator )

    def setDescription(self, title, description):
        self.obj.setDescription( title, description )
    
    def setNotes(self, title, notes):
        if not notes:
            return
        self.obj.setNotes( title, notes )

    def setRequirements(self, title, requirements):
        if not requirements:
            return
        self.obj.setRequirements(title, requirements)

    def setButtons(self):
        self.obj.setButtons()

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
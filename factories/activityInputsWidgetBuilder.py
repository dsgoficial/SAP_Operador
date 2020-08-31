from PyQt5 import QtWidgets, QtGui, QtCore
from Ferramentas_Producao.interfaces.IActivityInputsWidgetBuilder import IActivityInputsWidgetBuilder
from Ferramentas_Producao.widgets.activityInputs import ActivityInputs

class ActivityInputsWidgetBuilder(IActivityInputsWidgetBuilder):

    def __init__(self):
        super(ActivityInputsWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ActivityInputs()

    def setMediator(self, mediator):
        self.obj.setMediator( mediator )

    def setInputs(self, inputData):
        self.obj.setInputs( inputData )

    def adjustWidgets(self):
        self.obj.adjustWidgets()

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
from PyQt5 import QtWidgets, QtGui, QtCore
from Ferramentas_Producao.interfaces.IActivityDataWidgetBuilder import IActivityDataWidgetBuilder
from Ferramentas_Producao.widgets.activityData import ActivityData

class ActivityDataWidgetBuilder(IActivityDataWidgetBuilder):

    def __init__(self):
        super(ActivityDataWidgetBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ActivityData()

    def setController(self, controller):
        self.obj.setController( controller )

    def setStyles(self, styles):
        self.obj.setStyles(styles)

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
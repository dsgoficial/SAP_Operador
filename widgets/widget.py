from Ferramentas_Producao.interfaces.IWidget import IWidget
from PyQt5 import QtWidgets, QtGui, QtCore

class Widget(QtWidgets.QWidget, IWidget):

    def __init__(self, mediator):
        super(Widget, self).__init__()
        self.mediator = mediator

    def setMediator(self, mediator):
        self.mediator = mediator

    def getMediator(self):
        return self.mediator
from Ferramentas_Producao.widgets.widget import Widget
import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic

class ActivityRoutines(Widget):

    def __init__(self, mediator=None):
        super(ActivityRoutines, self).__init__(mediator)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        layout = QtWidgets.QHBoxLayout()
        self.openRoutinesBtn = QtWidgets.QPushButton('Abrir', self)
        self.openRoutinesBtn.clicked.connect(
            lambda: self.getMediator().notify(self, 'openRoutines')
        )
        layout.addWidget(self.openRoutinesBtn)
        layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                150, 
                20,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding
            )
        )
        self.layout.addLayout(layout)
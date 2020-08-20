from Ferramentas_Producao.widgets.widget import Widget
import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic

class ActivityData(Widget):

    def __init__(self, controller=None):
        super(ActivityData, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.controller = controller
        self.initWidget()
    
    def initWidget(self):
        self.loadStyles()

    def loadStyles(self):
        self.stylesCb.addItems(
            self.getController().getActivityStyles()
        )
        
    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'activityData.ui'
        )

    @QtCore.pyqtSlot(bool)
    def on_loadBtn_clicked(self):
        self.getController().loadActivityData(
            self.onlyWithGeomCkb.isChecked(),
            self.notLoadInputsCkb.isChecked(),
            self.stylesCb.currentText()
        )
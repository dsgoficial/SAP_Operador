from PyQt5 import QtWidgets, QtGui, QtCore, uic
import os

class ActivityDataSummary(QtWidgets.QDialog):

    def __init__(self, controller=None):
        super(ActivityDataSummary, self).__init__()
        uic.loadUi(self.getUiPath(), self)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'activityDataSummary.ui'
        )

    def addWidget(self, widget):
        self.scrollAreaContents.layout().addWidget(widget)

    def setLayerNames(self, title, layerNames):
        if not layerNames:
            return           
        self.addWidget(QtWidgets.QLabel("<b>{0}</b>".format(title), self))
        for name in layerNames:
            self.addWidget(QtWidgets.QLabel(name, self))
    
    def setRuleNames(self, title, ruleNames):
        if not ruleNames:
            return
        self.addWidget(QtWidgets.QLabel("<b>{0}</b>".format(title), self))
        for name in ruleNames:
            self.addWidget(QtWidgets.QLabel(name, self))

    def adjustWidgets(self):
        self.scrollAreaContents.layout().addSpacerItem(
            QtWidgets.QSpacerItem(
                20, 
                150,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding
            )
        )

   
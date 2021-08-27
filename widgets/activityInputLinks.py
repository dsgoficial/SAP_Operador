from Ferramentas_Producao.widgets.widget import Widget

from PyQt5 import QtWidgets, QtGui, QtCore, uic
import os, json

class ActivityInputLinks(Widget):

    def __init__(self, controller=None):
        super(ActivityInputLinks, self).__init__(controller)
        uic.loadUi(self.getUiPath(), self)
        self.inputData = []

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'activityInputLinks.ui'
        )

    def addWidget(self, widget):
        self.scrollAreaContents.layout().addWidget(widget)

    def setInputs(self, inputData):
        if not inputData:
            return
        for item in inputData:
            label = QtWidgets.QLabel(self)
            if item['tipo_insumo_id'] == 5:
                label.setText("<a href=\"{0}\">{1}</a>".format(item['caminho'], item['nome']))
                label.setOpenExternalLinks(True)
            else:
                label.setText(item['nome'])
            label.customData = json.dumps(item)
            self.addWidget(label)
        self.inputData = inputData

    def hasData(self):
        return self.inputData != []

    def adjustWidgets(self):
        self.scrollAreaContents.layout().addSpacerItem(
            QtWidgets.QSpacerItem(
                20, 
                150,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding
            )
        )
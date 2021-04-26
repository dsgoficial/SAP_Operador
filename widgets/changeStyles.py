from Ferramentas_Producao.widgets.widget import Widget

import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic

class ChangeStyles(Widget):

    def __init__(self, controller=None):
        super(ChangeStyles, self).__init__(controller)
        uic.loadUi(self.getUiPath(), self)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'changeStyles.ui'
        )

    def loadStyles(self, styles, defaultStyle):
        self.stylesCb.addItems(styles)
        self.stylesCb.setCurrentIndex(self.stylesCb.findText(defaultStyle))

    def page(self):
        nextIndex = self.stylesCb.currentIndex() + 1
        if nextIndex == self.stylesCb.count():
            self.stylesCb.setCurrentIndex(0)
            return
        self.stylesCb.setCurrentIndex(nextIndex)

    @QtCore.pyqtSlot(str)
    def on_stylesCb_currentTextChanged(self, text):
        self.getController().changeMapLayerStyle(text)
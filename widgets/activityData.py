from Ferramentas_Producao.widgets.widget import Widget
from Ferramentas_Producao.interfaces.IActivityDataWidget import IActivityDataWidget

import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic

class ActivityData(Widget, IActivityDataWidget):

    def __init__(self, mediator=None):
        super(ActivityData, self).__init__(mediator)
        uic.loadUi(self.getUiPath(), self)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'activityData.ui'
        )

    def setStyles(self, styles):
        self.stylesCb.addItems(styles)

    def onlyWithFeatures(self):
        return self.onlyWithGeomCkb.isChecked()

    def getStyle(self):
        return self.stylesCb.currentText()

    @QtCore.pyqtSlot(bool)
    def on_loadLayersBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.getMediator().notify( self, 'loadActivityLayers' )
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    @QtCore.pyqtSlot(bool)
    def on_summaryBtn_clicked(self):
        self.getMediator().notify( self, 'showActivityDataSummary' )
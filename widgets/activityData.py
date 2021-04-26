from Ferramentas_Producao.widgets.widget import Widget
from Ferramentas_Producao.interfaces.IActivityDataWidget import IActivityDataWidget

import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic

class ActivityData(Widget, IActivityDataWidget):

    def __init__(self, controller=None):
        super(ActivityData, self).__init__(controller)
        uic.loadUi(self.getUiPath(), self)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'activityData.ui'
        )

    def onlyWithFeatures(self):
        return self.onlyWithGeomCkb.isChecked()

    @QtCore.pyqtSlot(bool)
    def on_loadLayersBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.getController().loadActivityLayers(self.onlyWithFeatures())
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    @QtCore.pyqtSlot(bool)
    def on_summaryBtn_clicked(self):
        self.getController().showActivityDataSummary()
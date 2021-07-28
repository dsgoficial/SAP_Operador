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

    @QtCore.pyqtSlot(bool)
    def on_loadMenuBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.getController().loadMenu(
                self.menusCb.itemData( self.menusCb.currentIndex() )
            )
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def loadMenus(self, menus):
        self.setVisibleWidgetsLayout( self.menuLayout, True if menus else False )
        self.menusCb.clear()
        for item in menus:
            self.menusCb.addItem(
                item['nome'],
                item['definicao_menu']
            )

    def setVisibleWidgetsLayout(self, layout, visible):
        for idx in range(layout.count()):
            item = layout.itemAt(idx)
            widget = item.widget()
            if widget is None:
                continue
            widget.setVisible( visible )
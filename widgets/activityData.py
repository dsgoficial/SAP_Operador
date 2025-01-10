from SAP_Operador.widgets.widget import Widget
from SAP_Operador.interfaces.IActivityDataWidget import IActivityDataWidget

import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from .remoteLoadLayers import RemoteLoadLayers

class ActivityData(Widget, IActivityDataWidget):

    def __init__(self, controller=None, sap=None):
        super(ActivityData, self).__init__(controller)
        uic.loadUi(self.getUiPath(), self)
        self.loadReviewToolBtn.setVisible(False)
        self.sap = sap

    def setSap(self, sap):
        self.sap = sap

    def getSap(self):
        return self.sap

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'activityData.ui'
        )

    @QtCore.pyqtSlot(bool)
    def on_loadLayersBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            activityDataModel = self.sap.getActivityDataModel()
            camadasComuns = [l['nome'] for l in activityDataModel.getLayers() if ('camada_incomum' not in l or not l['camada_incomum'])]
            self.getController().loadActivityLayersByNames(camadasComuns)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    @QtCore.pyqtSlot(bool)
    def on_summaryBtn_clicked(self):
        activityDataModel = self.sap.getActivityDataModel()
        self.dlg = RemoteLoadLayers()
        self.dlg.loadLayers([l for l in activityDataModel.getLayers() if 'camada_incomum' in l and l['camada_incomum']])
        self.dlg.load.connect(self.getController().loadActivityLayersByNames)
        self.dlg.show()
        

    @QtCore.pyqtSlot(bool)
    def on_loadMenuBtn_clicked(self):
        self.getController().loadMenu()
    
    @QtCore.pyqtSlot(bool)
    def on_loadReviewToolBtn_clicked(self):
        self.getController().loadReviewTool()
    
    @QtCore.pyqtSlot(bool)
    def on_loadDSGToolsQAToolboxBtn_clicked(self):
        self.getController().loadDsgToolsQAToolbox()

    def setVisibleWidgetsLayout(self, layout, visible):
        for idx in range(layout.count()):
            item = layout.itemAt(idx)
            widget = item.widget()
            if widget is None:
                continue
            widget.setVisible( visible )

    def enabledMenuButton(self, enable):
        self.loadMenuBtn.setEnabled( enable )

    def enableWorkflowButton(self, enable):
        self.loadDSGToolsQAToolboxBtn.setEnabled(enable)

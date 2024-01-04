# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets

class RemoteLoadLayers(QtWidgets.QDialog):

    load = QtCore.pyqtSignal(list)

    def __init__(
            self
        ):
        super(RemoteLoadLayers, self).__init__()
        uic.loadUi(self.getUiPath(), self)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'remoteLoadLayers.ui'
        )

    def loadLayers(self, layers):
        self.layersW.addItems([
            l['nome'] for l in layers
        ])

    @QtCore.pyqtSlot(bool)
    def on_loadBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        layerNames = self.layersW.getSelections()
        if not layerNames:
            QtWidgets.QApplication.restoreOverrideCursor()
            return
        self.load.emit(layerNames)
        QtWidgets.QApplication.restoreOverrideCursor()
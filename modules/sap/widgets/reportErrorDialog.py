# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
from Ferramentas_Producao.modules.sap.widgets.sapDialog import SapDialog

class ReportErrorDialog(SapDialog):

    def __init__(
            self,
            controller,
            qgis
        ):
        super(ReportErrorDialog, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.controller = controller
        self.qgis = qgis
        self.wkt = None
        self.okBtn.clicked.connect(self.reportError)
        self.cancelBtn.clicked.connect(self.reject)
        self.makerBtn.clicked.connect(self.markError)
        self.okBtn.setEnabled(False)

    def setController(self, controller):
        self.controller = controller

    def getController(self):
        return self.controller

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'reportError.ui'
        )

    def loadErrorsTypes(self, errorsTypes):
        self.errorsTypesCb.clear()
        for item in errorsTypes:
            self.errorsTypesCb.addItem(
                item['tipo_problema'],
                item['tipo_problema_id']
            )
            
    def reportError(self):
        if not self.showQuestionMessageBox(
                'Aviso',
                '<p>Reportando um problema sua atividade atual será pausada, e você receberá uma nova atividade.</p>'
            ):
            return
        self.getController().reportError(
            self.errorsTypesCb.itemData(self.errorsTypesCb.currentIndex()),
            self.descrTe.toPlainText()
        )
        self.accept()

    def markError(self):
        tool = self.qgis.activeTool('SelectError')
        tool.selected.connect(self.setErrorWkt)

    def setErrorWkt(self, wkt):
        self.wkt = wkt
        self.okBtn.setEnabled(True)
        self.makerBtn.setStyleSheet('QPushButton { background-color: green }')
        self.qgis.activeTool('SelectError', True)
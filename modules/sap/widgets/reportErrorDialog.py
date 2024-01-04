# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
from Ferramentas_Producao.modules.sap.widgets.sapDialog import SapDialog

class ReportErrorDialog(SapDialog):

    reported = QtCore.pyqtSignal()

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
        self.finishErrorId = 'c72a8bcb-03c5-45df-abee-dafefe839cd1'
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

    @QtCore.pyqtSlot(int)
    def on_errorsTypesCb_currentIndexChanged(self, idx):
        if self.errorsTypesCb.itemText(idx) != 'Finalizei a atividade incorretamente':
            self.makerBtn.setVisible(True)
            self.obsLb.setVisible(True)
            self.okBtn.setEnabled(False)
            return
        self.makerBtn.setVisible(False)
        self.obsLb.setVisible(False)
        self.okBtn.setEnabled(True)
        
            
    def reportError(self):
        if not self.isValidInput():
            self.showErrorMessageBox(
                'Aviso',
                'Preencha todos os campos!'
            )
            return
        
        if self.errorsTypesCb.itemText(self.errorsTypesCb.currentIndex()) == 'Finalizei a atividade incorretamente':
            if not self.showQuestionMessageBox(
                    'Aviso',
                    '<p>O problema será reportado para o gerente, e você continuará com a atividade atual.</p>'
                ):
                return
            self.getController().incorrectEnding(self.descrTe.toPlainText())
            self.showInfoMessageBox(
                'Aviso',
                'O problema foi reportado, continue sua atividade atual.'
            )
            self.accept()
            return


        if not self.showQuestionMessageBox(
                'Aviso',
                '<p>Reportando um problema sua atividade atual será pausada, e você receberá uma nova atividade.</p>'
            ):
            return
        self.getController().reportError(
            self.errorsTypesCb.itemData(self.errorsTypesCb.currentIndex()),
            self.descrTe.toPlainText(),
            self.wkt
        )
        self.accept()
        self.reported.emit()

    def isValidInput(self):
        return self.descrTe.toPlainText() and (self.wkt or not self.makerBtn.isVisible())

    def markError(self):
        tool = self.qgis.activeTool('SelectError')
        tool.selected.connect(self.setErrorWkt)

    def setErrorWkt(self, wkt):
        self.wkt = wkt
        self.okBtn.setEnabled(True)
        self.makerBtn.setStyleSheet('QPushButton { background-color: green }')
        self.qgis.activeTool('SelectError', True)
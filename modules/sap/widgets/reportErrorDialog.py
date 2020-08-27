# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

class ReportErrorDialog(QtWidgets.QDialog):

    def __init__(
            self,
            controller,
            messageFactory=UtilsFactory().createMessageFactory()
        ):
        super(ReportErrorDialog, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.controller = controller
        self.messageFactory = messageFactory
        self.buttonBox.accepted.connect(
            self.reportError
        )

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
        for item in errorsTypes:
            self.errorsTypesCb.addItem(
                item['tipo_problema'],
                item['tipo_problema_id']
            )

    def showQuestionMessageBox(self, title, message):
        questionMessageBox = self.messageFactory.createQuestionMessageBox()
        return questionMessageBox.show(self, title, message)
            
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
            
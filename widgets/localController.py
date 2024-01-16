from Ferramentas_Producao.widgets.widget import Widget
from PyQt5 import QtWidgets, QtGui, QtCore, uic
import os, json

class LocalController(Widget):

    def __init__(self, controller=None):
        super(LocalController, self).__init__(controller)
        uic.loadUi(self.getUiPath(), self)
        self.setData(self.getController().getControllerInfo())
        
    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'controller.ui'
        )

    def setData(self, data):
        startTime = data[0]
        endTime = data[1]
        userName = data[2]
        userId = data[3]
        self.startDateDe.setDateTime(QtCore.QDateTime.fromSecsSinceEpoch(startTime)) if startTime else ''
        self.endDateDe.setDateTime(QtCore.QDateTime.fromSecsSinceEpoch(endTime)) if endTime else ''
        self.userLe.setText(userName) if userName else ''
        self.userIdLe.setText(userId) if userId else ''

    @QtCore.pyqtSlot(bool)
    def on_saveBtn_clicked(self):
        if not (
                self.userLe.text() and
                self.userIdLe.text()
            ):
            self.showError('Aviso', 'Preencha todos os dados!')
            return
        self.getController().saveControllerInfo(
            self.userLe.text(),
            self.userIdLe.text(),
            self.startDateDe.dateTime().toUTC().toString(QtCore.Qt.ISODate),
            self.endDateDe.dateTime().toUTC().toString(QtCore.Qt.ISODate)#.toSecsSinceEpoch()
        )
        self.showInfo('Aviso', 'Salvo com sucesso!')
from PyQt5 import QtWidgets, uic, QtGui, QtCore
import os
from Ferramentas_Producao.modules.sap.widgets.sapDialog import SapDialog

class EndActivityDialog(SapDialog):

    def __init__(self, controller=None, activeObs=False):
        super(EndActivityDialog, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.controller = controller
        self.endBtn.setEnabled(False)
        self.nameLe.textEdited.connect(self.updateEndButton)
        self.withoutCorrection = False
        self.activityDataModel = self.controller.getActivityDataModel()
        stepTypeId = self.activityDataModel.getStepTypeId()
        self.revisionW.setVisible(activeObs)
        self.resize(502, 141)

    def setController(self, controller):
        self.controller = controller

    def getController(self):
        return self.controller
    
    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'endActivityDialog.ui'
        )
    
    def updateEndButton(self):
        if self.getController().getUserName().lower() == self.nameLe.text():
            self.endBtn.setEnabled(True)
        else:
            self.endBtn.setEnabled(False)

    def getData(self):
        data = {
            'atividade_id' : self.activityDataModel.getId(),
            'sem_correcao' : self.withoutCorrection,
        }
        if self.changeFlowCb.currentIndex() != 0:
            data['alterar_fluxo'] = self.changeFlowCb.currentText()
        obs = self.obsTe.toPlainText()
        if obs:
            data['observacao_proxima_atividade'] = obs
        return data

    @QtCore.pyqtSlot(bool)
    def on_endBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.endBtn.setEnabled(False)
        try:
            self.getController().endActivity(self.getData())
            QtWidgets.QApplication.restoreOverrideCursor()
            self.endBtn.setEnabled(True)
            self.accept()
        except Exception as e:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.showErrorMessageBox('Erro', str(e))

    def clear(self):
        self.nameLe.setText('')
        
    def closeEvent(self, e):
        self.clear()

    def setWithoutCorrection(self, withoutCorrection):
        self.withoutCorrection = withoutCorrection

    
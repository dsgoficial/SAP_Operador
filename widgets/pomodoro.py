import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from Ferramentas_Producao.timers.timer import Timer
from Ferramentas_Producao.modules.qgis.qgisCtrl import QgisCtrl
from datetime import datetime
import json

class Pomodoro(QtWidgets.QWidget):

    def __init__(
            self,
            qgis=QgisCtrl()
        ):
        super(Pomodoro, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.qgis = qgis
        self.pomodoro = 0
        self.paused = False
        self.timeOnSeconds = 25 * 60
        self.pause1OnSeconds = 5 * 60
        self.pause2OnSeconds = 15 * 60
        self.currentTime = self.timeOnSeconds
        self.setCronText(self.getFormatedTime())
        self.cronTimer = Timer()
        self.cronTimer.addCallback(self.showTime)
        self.pauseTimer = Timer()
        self.startBtn.setVisible(True)
        self.pauseBtn.setVisible(False)
        self.restoreState()
        self.setInfoText('Pomodoros: {}'.format(self.pomodoro))
        
    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'pomodoro.ui'
        )

    def showTime(self):
        self.currentTime -= 1
        if self.currentTime == 0 and not self.paused:
            self.pomodoro += 1
            self.saveState()
            self.setInfoText('Pomodoros: {}'.format(self.pomodoro))
            self.currentTime = self.pause2OnSeconds if (self.pomodoro % 5) == 0 else self.pause1OnSeconds
            self.paused = True
            self.setStatusText('Pausa {}'.format('Longa' if (self.pomodoro % 5) == 0 else 'Curta'))
        elif self.currentTime == 0 and self.paused:
            self.paused = False
            self.currentTime = self.timeOnSeconds
            self.setStatusText('')
        self.setCronText(self.getFormatedTime())

    def saveState(self):
        now = datetime.now()
        date = now.strftime("%d-%m-%Y")
        self.qgis.setSettingsVariable(
            'productiontools:pomodoro', 
            json.dumps({
                date: self.pomodoro
            })
        )

    def restoreState(self):
        dumpData = self.qgis.getSettingsVariable('productiontools:pomodoro')
        if not dumpData:
            return
        data = json.loads(dumpData)
        self.pomodoro = list(data.values())[0]

    def getFormatedTime(self):
        return '{}:{}'.format(int(self.currentTime/60), str(round((float("{:.2f}".format(self.currentTime/60)) % 1) * 60)).zfill(2) )

    def setCronText(self, value):
        self.cronLb.setText(
            '''
            <html><head/><body><p align="center"><span style=" font-size:48pt; font-weight:600;">{}</span></p></body></html>
            '''.format(value)
        )

    def setStatusText(self, value):
        self.statusLb.setText(
            '''
            <html><head/><body><p align="center"><span style=" font-size:12pt; font-weight:600;">{}</span></p></body></html>
            '''.format(value)
        )

    def setInfoText(self, value):
        self.infoLb.setText(
            '''
            <html><head/><body><p align="center"><span style=" font-size:12pt; font-weight:600;">{}</span></p></body></html>
            '''.format(value)
        )

    @QtCore.pyqtSlot(bool)
    def on_startBtn_clicked(self):
        self.cronTimer.start(self.timeOnSeconds)
        self.startBtn.setVisible(False)
        self.pauseBtn.setVisible(True)

    @QtCore.pyqtSlot(bool)
    def on_restartBtn_clicked(self):
        self.cronTimer.stop()
        self.currentTime = self.timeOnSeconds
        self.setCronText(self.getFormatedTime())
        self.startBtn.setVisible(True)
        self.pauseBtn.setVisible(False)

    @QtCore.pyqtSlot(bool)
    def on_pauseBtn_clicked(self):
        self.cronTimer.stop()
        self.startBtn.setVisible(True)
        self.pauseBtn.setVisible(False)
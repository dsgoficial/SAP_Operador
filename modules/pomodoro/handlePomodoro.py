import time
from datetime import date, timedelta
from PyQt5.QtCore import QThread, pyqtSignal
from qgis.core import QgsSettings
from .userHistoric import UserHistoric


class HandlePomodoro(QThread, UserHistoric):

    updateTimer = pyqtSignal(int)
    updateHistoric = pyqtSignal(list)

    # TODO Start this thread just after pressing the pomodoro button

    def __init__(self, parent=None):
        super(HandlePomodoro, self).__init__(parent)
        self.running = True
        # TODO: Use QTimer()
        self.duration = 1500
        self.today = date.today
        self.isTimerRunning = False
        # TODO: use a simple array
        self.session = {
            'historic': []
        }

    def run(self):
        while self.running:
            if self.duration:
                for i in range(self.duration):
                    if self.isTimerRunning:
                        self.updateTimer.emit(i)
                        self.duration -= 1
                        if not self.duration:
                            self.triggerSuccess()
                            self.isTimerRunning = False
                    QThread.sleep(1)
            else:
                QThread.sleep(1)
                continue

        # timer = QTimer(self)
        # timer.setInterval(1000)
        # timer.timeout.connect(self.updateText)
        # timer.start()

    def refreshPomodoroByButton(self, isMonitoring=True):
        # TODO: append the pixmap itself
        if isMonitoring and self.duration and self.duration != 1500:
            self.triggerFail()
        self.duration = 1500
        self.isTimerRunning = True

    def refreshPomodoroByMonitor(self, isMonitoring=True):
        self.isTimerRunning = False
        if self.duration:
            self.triggerFail()

    def triggerSuccess(self):
        self.updateSucess()
        self.session['historic'].append(True)
        self.updateHistoric.emit(self.session['historic'])

    def triggerFail(self):
        self.updateFail()
        if self.duration:
            self.session['historic'].append(False)
        self.updateHistoric.emit(self.session['historic'])

    def lcdString(self):
        return '{:2}:{:0>2}'.format(self.duration // 60, self.duration % 60)
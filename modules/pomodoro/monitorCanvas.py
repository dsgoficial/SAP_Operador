from qgis.PyQt.QtCore import QThread, pyqtSignal
from qgis.utils import iface
from .userHistoric import UserHistoric


class MonitorCanvas(QThread, UserHistoric):

    updateByMonitor = pyqtSignal()
    updateTickTimer = pyqtSignal()

    def __init__(self, parent=None):
        super(MonitorCanvas, self).__init__(parent)
        self.iface = iface
        self.running = True
        self.isMonitoring = True
        self.hasChangedCanvas = False

    def startMonitoring(self):
        self.isMonitoring = True
        self.hasChangedCanvas = True
        #print('Started monitoring')
        iface.mapCanvas().mapCanvasRefreshed.connect(self.updateMonitoring)

    def stopMonitoring(self):
        self.isMonitoring = False
        #print('Stopped monitoring')
        # try:
        #     iface.mapCanvas().mapCanvasRefreshed.disconnect(self.updateMonitoring)
        # except TypeError:
        #     pass

    def updateMonitoring(self):
        self.hasChangedCanvas = True

    def run(self):
        # TODO Verificar a lógica. stopMonitonitor is not called after the emit
        # TODO Verificar a lógica. UpdateTickTimer não é chamado no primeiro pomodoro
        while self.running:
            if self.hasChangedCanvas:
                self.hasChangedCanvas = False
                self.updateWorkTime()
                self.updateTickTimer.emit()
                #print('Updating work time!')
                QThread.sleep(60)
            elif not self.hasChangedCanvas and not self.isMonitoring:
                self.updateIdleTime()
                self.updateTickTimer.emit()
                #print('Updating idle time!')
                QThread.sleep(60)
            elif not self.hasChangedCanvas and self.isMonitoring:
                self.stopMonitoring()
                self.updateByMonitor.emit()

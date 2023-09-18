from qgis.PyQt import QtCore
from qgis.utils import iface
from Ferramentas_Producao.timers.timer import Timer
from Ferramentas_Producao.modules.qgis.qgisApi import QgisApi
from datetime import datetime
import json

class Canvas(QtCore.QObject):

    changeStatus = QtCore.pyqtSignal(int, int)

    def __init__(
            self,
            qgis=None
        ):
        super(Canvas, self).__init__()
        self.qgis = QgisApi() if qgis is None else qgis
        self.hasChangedCanvas = False
        self.minutesActive = 0
        self.minutesNoActive = 0
        self.cronTimer = Timer()
        self.cronTimer.addCallback(self.checkState) 
        
    def start(self):
        self.stop()
        self.restoreState()
        self.changeStatus.emit(self.minutesActive, self.minutesNoActive)
        self.cronTimer.start(60 * 1000)
        iface.mapCanvas().mapCanvasRefreshed.connect(self.changeCanvas)

    def changeCanvas(self):
        self.hasChangedCanvas = True

    def checkState(self):
        if self.hasChangedCanvas:
            self.minutesActive += 1 
            self.hasChangedCanvas = False
        else:
            self.minutesNoActive += 1 
        self.changeStatus.emit(self.minutesActive, self.minutesNoActive)
        self.saveState()
            
    def stop(self):
        self.cronTimer.stop()
        try:
            iface.mapCanvas().mapCanvasRefreshed.disconnect(self.changeCanvas)
        except:
            pass

    def saveState(self):
        date = self.getCurrentDate()
        self.qgis.setSettingsVariable(
            'productiontools:monitoring:canvas:v2', 
            json.dumps({
                date: [
                    self.minutesActive,
                    self.minutesNoActive
                ]
            })
        )

    def getCurrentDate(self):
        now = datetime.now()
        return now.strftime("%d-%m-%Y")

    def restoreState(self):
        dumpData = self.qgis.getSettingsVariable('productiontools:monitoring:canvas:v2')
        if not dumpData:
            return
        dumpData = json.loads(dumpData)
        date = self.getCurrentDate()
        if not(date in dumpData):
            return
        self.minutesActive = dumpData[date][0]
        self.minutesNoActive = dumpData[date][1]
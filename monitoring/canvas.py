from qgis.PyQt import QtCore
from qgis.utils import iface
from SAP_Operador.timers.timer import Timer
from SAP_Operador.modules.qgis.qgisApi import QgisApi
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
        data = self._loadData()
        data[date] = [self.minutesActive, self.minutesNoActive]
        self.qgis.setSettingsVariable(
            'productiontools:monitoring:canvas:v2',
            json.dumps(data)
        )

    def getCurrentDate(self):
        now = datetime.now()
        return now.strftime("%d-%m-%Y")

    def _loadData(self):
        dumpData = self.qgis.getSettingsVariable('productiontools:monitoring:canvas:v2')
        if not dumpData:
            return {}
        try:
            data = json.loads(dumpData)
        except (ValueError, TypeError):
            return {}
        return data if isinstance(data, dict) else {}

    def restoreState(self):
        data = self._loadData()
        date = self.getCurrentDate()
        if date not in data:
            self.minutesActive = 0
            self.minutesNoActive = 0
            return
        self.minutesActive = data[date][0]
        self.minutesNoActive = data[date][1]
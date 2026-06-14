from qgis.PyQt import QtCore
from qgis.utils import iface
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)
from datetime import datetime

from SAP_Operador.timers.timer import Timer
from SAP_Operador.monitoring.buffer import MonitoringBuffer

BUFFER_KEY = 'productiontools:monitoring:tela:buffer'
SAMPLE_INTERVAL = 30 * 1000
FLUSH_SIZE = 5


class Screen(QtCore.QObject):
    """Captura de microcontrole por tela.

    A cada 30s, se ha atividade ativa e o canvas mudou desde a ultima amostra,
    captura o extent e a escala (zoom) do canvas com a data atual. Acumula os
    pontos e da flush em lote (a cada 5 pontos ou no stop). Se o envio falhar
    (sem rede), o lote e bufferizado em QSettings e reenviado depois.
    """

    def __init__(self, activityId, sap, qgis=None):
        super(Screen, self).__init__()
        self.activityId = activityId
        self.sap = sap
        self.buffer = MonitoringBuffer(BUFFER_KEY, qgis)
        self.points = []
        self.hasChangedCanvas = False
        self.cronTimer = Timer()
        self.cronTimer.addCallback(self.sample)

    def start(self):
        self.stop()
        self.cronTimer.start(SAMPLE_INTERVAL)
        iface.mapCanvas().mapCanvasRefreshed.connect(self.changeCanvas)

    def changeCanvas(self):
        self.hasChangedCanvas = True

    def sample(self):
        if not self.hasChangedCanvas:
            return
        self.hasChangedCanvas = False
        canvas = iface.mapCanvas()
        extent = canvas.extent()
        # A coluna monitoramento_tela.geom e' EPSG:4326 e o backend monta
        # ST_MakeEnvelope(...,4326); o canvas costuma estar em UTM, entao
        # reprojeta o extent para 4326 antes de enviar.
        src = canvas.mapSettings().destinationCrs()
        dst = QgsCoordinateReferenceSystem('EPSG:4326')
        if src.isValid() and src != dst:
            transform = QgsCoordinateTransform(src, dst, QgsProject.instance())
            extent = transform.transformBoundingBox(extent)
        self.points.append({
            'data': datetime.now().astimezone().isoformat(),
            'x_min': extent.xMinimum(),
            'x_max': extent.xMaximum(),
            'y_min': extent.yMinimum(),
            'y_max': extent.yMaximum(),
            'zoom': canvas.scale()
        })
        if len(self.points) >= FLUSH_SIZE:
            self.flush()

    def _send(self, payload):
        self.sap.saveScreenTrack(payload)

    def flush(self):
        if not self.points:
            self.buffer.flush(self._send)
            return
        payload = {
            'atividade_id': self.activityId,
            'dados': self.points
        }
        try:
            self._send(payload)
            self.points = []
            self.buffer.flush(self._send)
        except Exception:
            self.buffer.add(payload)
            self.points = []

    def stop(self):
        self.cronTimer.stop()
        try:
            iface.mapCanvas().mapCanvasRefreshed.disconnect(self.changeCanvas)
        except (TypeError, RuntimeError):
            pass
        self.flush()

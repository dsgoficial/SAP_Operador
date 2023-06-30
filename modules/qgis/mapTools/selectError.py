from qgis.core import QgsFeature, QgsGeometry
from qgis.gui import QgsMapToolIdentify
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtWidgets
from qgis.utils import iface
from qgis import gui, core
import math
from PyQt5.QtGui import QColor

from Ferramentas_Producao.modules.qgis.mapTools.mapTool import MapTool

class SelectError(QgsMapToolIdentify, MapTool):

    selected = pyqtSignal(str)
    
    def __init__(self):
        super(SelectError, self).__init__(iface.mapCanvas())
        self.setCursor(Qt.CrossCursor)
        self.rubberBand = None
        self.snapCursorRubberBand = None
        self.transform = core.QgsCoordinateTransform(
            iface.mapCanvas().mapSettings().destinationCrs(), 
            core.QgsCoordinateReferenceSystem("EPSG:4326"),
            core.QgsProject.instance()
        )
        self.initVariable()

    def initVariable(self):
        self.points = []
        self.startPoint = None
        self.endPoint = None
        if not self.rubberBand:
            return
        self.rubberBand.reset()
        self.rubberBand = None
        
    def showCircle(self, startPoint, endPoint):
        nPoints = 50
        x = startPoint.x()
        y = startPoint.y()
        r = math.sqrt((endPoint.x() - startPoint.x())**2 + (endPoint.y() - startPoint.y())**2)
        self.rubberBand.reset(core.QgsWkbTypes.PolygonGeometry)
        self.points = []

        for itheta in range(nPoints+1):
            theta = itheta*(2.0*math.pi/nPoints)
            point = core.QgsPointXY(x+r*math.cos(theta), y+r*math.sin(theta))
            self.rubberBand.addPoint(self.transform.transform(point))
            self.points.append(point)
        self.rubberBand.closePoints()

    def getRubberBand(self):
        rubberBand = gui.QgsRubberBand(iface.mapCanvas(), core.QgsWkbTypes.PolygonGeometry)
        rubberBand.setFillColor(QColor(255, 0, 0, 40))
        rubberBand.setSecondaryStrokeColor(QColor(255, 0, 0, 200))
        rubberBand.setWidth(2)
        return rubberBand

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.initVariable()
            return
  
    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.startPoint:
                return
            self.startPoint = core.QgsPointXY(event.mapPoint())
            self.rubberBand = self.getRubberBand()
            return
        if event.button() == Qt.RightButton:
            self.execute()
            self.initVariable()

    def getSnapRubberBand(self):
        rubberBand = gui.QgsRubberBand(iface.mapCanvas(), geometryType=core.QgsWkbTypes.PointGeometry)
        rubberBand.setFillColor(QColor(255, 0, 0, 40))
        rubberBand.setSecondaryStrokeColor(QColor(255, 0, 0, 200))
        rubberBand.setWidth(2)
        rubberBand.setIcon(gui.QgsRubberBand.ICON_X)
        return rubberBand

    def createSnapCursor(self, point):
        self.snapCursorRubberBand = self.getSnapRubberBand()
        self.snapCursorRubberBand.addPoint(point)
               
    def canvasMoveEvent(self, event):
        if self.snapCursorRubberBand:
            self.snapCursorRubberBand.hide()
            self.snapCursorRubberBand.reset(geometryType=core.QgsWkbTypes.PointGeometry)
            self.snapCursorRubberBand = None
        oldPoint = core.QgsPointXY(event.mapPoint())
        event.snapPoint()
        point = core.QgsPointXY(event.mapPoint())
        if oldPoint != point:
            self.createSnapCursor(point)
        if self.startPoint:
            self.endPoint = core.QgsPointXY(event.mapPoint())
            self.showCircle(self.startPoint, self.endPoint)

    def execute(self):
        errorPolygon = 'SRID=4326;{}'.format(
            QgsGeometry.fromPolygonXY([self.points]).asWkt()
        )
        self.selected.emit(errorPolygon)
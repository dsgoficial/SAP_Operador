from qgis.core import QgsFeature
from qgis.gui import QgsMapToolIdentify
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from qgis.utils import iface
from qgis import gui, core
import math
from PyQt5.QtGui import (
    QColor
)

from SAP_Operador.modules.qgis.mapTools.mapTool import MapTool

class ConvergencePoint(QgsMapToolIdentify, MapTool):
    
    def __init__(self):
        super(ConvergencePoint, self).__init__(iface.mapCanvas())
        self.setCursor(Qt.CrossCursor)
        self.rubberBand = None
        self.snapCursorRubberBand = None
        self.initVariable()

    def isValidParameters(self, parameters):
        if not parameters:
            return (False, 'Selecione no mínimo uma feição')
        elif [data['layer'] for data in parameters if not(data['layer'].isEditable())]:
            return (False, 'Todas as camadas selecionadas devem está no modo editável')
        return (True, '')

    def getParameters(self):
        return [
            {
                'layer': layer,
                'features': layer.selectedFeatures()
            }
            for layer in iface.mapCanvas().layers()
            if (
                not( layer.type() == core.QgsMapLayer.RasterLayer)
                and
                len(layer.selectedFeatures()) > 0
            )
        ]

    def activate(self):
        super().activate()
        self.parameters = self.getParameters()
        result = self.isValidParameters(self.parameters)
        if result[0]:
            return
        self.showErrorMessageBox(
            iface.mainWindow(),
            'Erro',
            result[1]
        )
        iface.mapCanvas().unsetMapTool(self)
        
    def initVariable(self):
        self.parameters = []
        self.featuresSelected = []
        self.startPoint = None
        self.endPoint = None
        if not self.rubberBand:
            return
        self.rubberBand.reset(True)
        self.rubberBand = None
        
    def showCircle(self, startPoint, endPoint):
        nPoints = 50
        x = startPoint.x()
        y = startPoint.y()
        r = math.sqrt((endPoint.x() - startPoint.x())**2 + (endPoint.y() - startPoint.y())**2)
        self.rubberBand.reset(core.QgsWkbTypes.PolygonGeometry)

        for itheta in range(nPoints+1):
            theta = itheta*(2.0*math.pi/nPoints)
            self.rubberBand.addPoint(core.QgsPointXY(x+r*math.cos(theta), y+r*math.sin(theta)))
        self.rubberBand.closePoints()

    def getRubberBand(self):
        rubberBand = gui.QgsRubberBand(iface.mapCanvas(), True)
        rubberBand.setFillColor(QColor(255, 0, 0, 40))
        rubberBand.setSecondaryStrokeColor(QColor(255, 0, 0, 200))
        rubberBand.setWidth(2)
        return rubberBand
  
    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.startPoint:
                self.startPoint = core.QgsPointXY(event.mapPoint())
                self.rubberBand = self.getRubberBand()
        if event.button() == Qt.RightButton:
            self.execute(self.rubberBand.asGeometry(), self.parameters)
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

    def execute(self, geometryFilter, parameters):
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            convergencePoint = self.mapFunctionsFactory.getFunction('ConvergencePoint')
            result = convergencePoint.run(geometryFilter, parameters)
            if not result[0]:
                self.showErrorMessageBox(
                    iface.mainWindow(),
                    'Erro',
                    result[1]
                )
        finally:    
            QtWidgets.QApplication.restoreOverrideCursor()
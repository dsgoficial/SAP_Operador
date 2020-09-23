from qgis.core import (
    QgsWkbTypes,
    QgsFeatureRequest,
    QgsFeature,
    QgsRectangle,
    QgsCoordinateTransform,
    QgsPoint,
    QgsGeometry,
    QgsProject
)

from qgis.gui import (
    QgsRubberBand
)

from PyQt5.QtCore import (
    QTimer,
    QVariantAnimation,
    Qt
)

from PyQt5.QtGui import (
    QColor
)

from qgis.utils import iface

class FlashFeature:

    def __init__(self):
        pass

    def finishedAnimation(self, animation, rb):
            animation.deleteLater()
            rb.reset()
            del rb
            iface.mapCanvas().refresh()

    def valueChangedAnimation(self, value, animation, rb, geomType):
        c = value
        if ( geomType == QgsWkbTypes.PolygonGeometry ):
            rb.setFillColor( c )
        else:
            rb.setStrokeColor( c )
            c = rb.secondaryStrokeColor()
            c.setAlpha( c.alpha() )
            rb.setSecondaryStrokeColor( c )
        rb.update()

    def getFeature(self, featureId, layer):
        it = layer.getFeatures( QgsFeatureRequest().setFilterFids( [featureId] ).setNoAttributes() )
        f = QgsFeature()
        it.nextFeature(f)
        return f

    def setCanvasExtent(self, featureGeometry, layerCrs):
        xmin, ymin, xmax, ymax = featureGeometry.boundingBox().toRectF().getCoords()
        canvasCrs = iface.mapCanvas().mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(layerCrs, canvasCrs, QgsProject.instance())
        txmin, tymin = transform.transform(float(xmin), float(ymin))
        txmax, tymax = transform.transform(float(xmax), float(ymax))
        rect = QgsRectangle(txmin, tymin,txmax, tymax)
        iface.mapCanvas().setExtent(rect)

    def getFeatureMarkerPoint(self, featureGeometry, layerCrs):
        canvasCrs = iface.mapCanvas().mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(layerCrs, canvasCrs, QgsProject.instance())
        geomType = QgsWkbTypes.geometryType(featureGeometry.wkbType())
        if geomType == QgsWkbTypes.LineGeometry:
            multiPoints = featureGeometry.convertToType(0, True)
            pointList = multiPoints.asMultiPoint()
            return transform.transform(pointList[int(len(pointList)/2)])
        else:
            return transform.transform(featureGeometry.centroid().asPoint())

    def showCrossedLines(self, point):
        currExt = iface.mapCanvas().extent()

        leftPt = QgsPoint(currExt.xMinimum(), point.y())
        rightPt = QgsPoint(currExt.xMaximum(), point.y())
        topPt = QgsPoint(point.x(), currExt.yMaximum())
        bottomPt = QgsPoint(point.x(), currExt.yMinimum())
        horizLine = QgsGeometry.fromPolyline([leftPt, rightPt])
        vertLine = QgsGeometry.fromPolyline([topPt, bottomPt])
        
        crossRb = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.LineGeometry)
        crossRb.setColor(Qt.red)
        crossRb.setWidth(2)
        crossRb.addGeometry(horizLine, None)
        crossRb.addGeometry(vertLine, None)
        QTimer.singleShot(1500, lambda r=crossRb: r.reset())

    def startFlashFeature(self, featureGeometry, layerCrs):
        geomType = QgsWkbTypes.geometryType(featureGeometry.wkbType())
        rb = QgsRubberBand(iface.mapCanvas(), geomType)
        rb.addGeometry( featureGeometry, layerCrs )
        flashes=3
        duration=500
        if geomType == QgsWkbTypes.LineGeometry or geomType == QgsWkbTypes.PointGeometry:
            rb.setWidth( 2 )
            rb.setSecondaryStrokeColor( QColor( 255, 255, 255 ) )
        if geomType == QgsWkbTypes.PointGeometry :
            rb.setIcon( QgsRubberBand.ICON_CIRCLE )
        startColor = QColor(255, 0, 0, 255)
        startColor.setAlpha( 255 )
        endColor = QColor(255, 0, 0, 0)
        endColor.setAlpha( 0 )
        self.animation = QVariantAnimation( iface.mapCanvas() )
        self.animation.finished.connect(lambda a=self.animation, b=rb: self.finishedAnimation(a, b))
        self.animation.valueChanged.connect(lambda value, a=self.animation, b=rb, c=geomType: self.valueChangedAnimation(value, a, b, c))
        self.animation.setDuration( duration * flashes )
        self.animation.setStartValue( endColor )
        midStep = 0.2 / flashes
        for i in range(flashes):
            start = float(i  / flashes)
            self.animation.setKeyValueAt( start + midStep, startColor )
            end = float(( i + 1 ) / flashes)
            if not(end == 1.0):
                self.animation.setKeyValueAt( end, endColor )
        self.animation.setEndValue( endColor )
        self.animation.start()

    def execute(self, layer, feature):   
        layerCrs = layer.crs()
        feature = self.getFeature(feature.id(), layer)
        featureGeometry = feature.geometry()
        self.setCanvasExtent(featureGeometry, layerCrs)
        self.showCrossedLines(self.getFeatureMarkerPoint(featureGeometry, layerCrs))
        self.startFlashFeature(featureGeometry, layerCrs)
        
####
#selector = QgsGui.shortcutsManager().listAll()[175]
#QgsGui.shortcutsManager().setObjectKeySequence(selector, 'S')
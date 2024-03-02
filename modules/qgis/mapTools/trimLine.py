from qgis.core import QgsFeature
from qgis.gui import QgsMapToolIdentify
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from qgis.utils import iface
from qgis import gui, core

from SAP_Operador.modules.qgis.mapTools.mapTool import MapTool

class TrimLine(QgsMapToolIdentify, MapTool):
    
    def __init__(self):
        super(TrimLine, self).__init__(iface.mapCanvas())
        self.setCursor(Qt.CrossCursor)
        self.selectedFeatureIds = []

    def canvasReleaseEvent(self, event):
        foundFeatures = self.identify(event.x(), event.y(), self.ActiveLayer, self.VectorLayer)
        if not foundFeatures:
            self.cleanSelections()
            return
        validFeatures = [
            feat
            for feat in foundFeatures
            if feat.mLayer.geometryType() == core.QgsWkbTypes.LineGeometry
        ]
        if not validFeatures:
            return
        feature = validFeatures[0].mFeature
        layer = validFeatures[0].mLayer
        if feature.id() in self.selectedFeatureIds:
            layer.deselect(feature.id())
            self.selectedFeatureIds.remove(feature.id())        
            return
        layer.select(feature.id())
        self.selectedFeatureIds.append(feature.id())
        if not(len(self.selectedFeatureIds) == 2):
            return
        self.execute()
        self.cleanSelections()

    def cleanSelections(self):
        self.removeAllSelection()
        self.selectedFeatureIds = []

    def execute(self):
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            featureToTrimId = self.selectedFeatureIds[0]
            featureTargetId = self.selectedFeatureIds[1]
            distanceTolerance = 10
            trimLine = self.mapFunctionsFactory.getFunction('TrimLine')
            result = trimLine.run(featureToTrimId, featureTargetId, distanceTolerance)
            if not result[0]:
                self.showErrorMessageBox(
                    iface.mainWindow(),
                    'Erro',
                    result[1]
                )
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        
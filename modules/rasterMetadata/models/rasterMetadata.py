import json
import os
from qgis.core import QgsGeometry, QgsCoordinateTransform, QgsProject

class RasterMetadata:

    def __init__(self, controller=None):
        self.layers = []
        self.controller = controller
        self.addedFeaturesList = []

    def setController(self, controller):
        self.controller = controller

    def getController(self):
        return self.controller

    def setLayers(self, layers):
        self.layers = layers

    def getLayers(self):
        return self.layers

    def connectLayersSignal(self):
        for lyr in self.getLayers():
            lyr.featureAdded.connect(
                self.storeFeatureId
            )
            lyr.editCommandEnded.connect(self.loadMetadata)

    def disconnectLayersSignal(self):
        for lyr in self.getLayers():
            try:
                lyr.featureAdded.disconnect(
                    self.storeFeatureId
                )
            except:
                pass
            try:
                lyr.editCommandEnded.disconnect(self.loadMetadata)
            except:
                pass
        
    def getStoragePath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'config.json'
        )

    def isJSON(self, data):
        try:
            json.loads(data)
            return True
        except:
            return False

    def setConfig(self, data):
        if not self.isJSON(data):
            raise 'A entrada deve ser do tipo "JSON"'
        with open(self.getStoragePath(), 'w') as f:
            f.write(data)

    def getConfig(self):
        with open(self.getStoragePath(), 'r') as f:
            data = f.read()
            if not data:
                return {}
            return json.loads(data)

    def getConfigText(self):
        return json.dumps(self.getConfig(), indent=4)
    
    def storeFeatureId(self, featId):
        self.addedFeaturesList.append(featId)

    def loadMetadata(self):
        while self.addedFeaturesList != []:
            featureId = self.addedFeaturesList.pop()
            try:
                if featureId >= 0:
                    return
                layer = self.getController().getActiveVectorLayer()
                if not layer:
                    raise Exception('Não há um "VectorLayer" ativo!')
                if not layer.isEditable():
                    return
                config = self.getConfig()
                if not(layer.name() in config['camadas']):
                    return
                feature = layer.getFeature(featureId)
                if not feature.isValid():
                    return
                rasters = self.getController().getVisibleRasters()
                if len(rasters) != 1:
                    raise Exception('Para carregar o metadados da image deve haver um, e apenas um, "RasterLayer" visível!')
                raster = rasters[0]
                if not(raster.name() in config['metadata']):
                    return
                layerCrs = layer.crs()
                rasterCrs = raster.crs()
                rasterExtent = raster.extent()
                rasterExtentGeom = QgsGeometry.fromRect(rasterExtent)
                if rasterCrs != layerCrs:
                    coordinateTransformer = QgsCoordinateTransform(
                        rasterCrs, layerCrs, QgsProject.instance()
                    )
                    rasterExtentGeom.transform(coordinateTransformer)
                geom = feature.geometry()
                if not geom.intersects(rasterExtentGeom):
                    raise Exception('O raster ativo não intersecta a feição adquirida!')
                for attribute in config['metadata'][raster.name()]:
                    fieldIdx = feature.fields().indexOf(attribute['nome'])
                    if fieldIdx < 0:
                        continue
                    feature[attribute['nome']] = attribute['valor']
                layer.beginEditCommand("FP: Guarda metadado da imagem na camada")
                layer.updateFeature(feature)
                layer.endEditCommand()
                self.getController().canvasRefresh() 
            except Exception as e:
                self.getController().showErrorMessageBox(str(e))
          
         

    
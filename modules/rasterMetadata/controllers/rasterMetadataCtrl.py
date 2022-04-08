from Ferramentas_Producao.modules.qgis.qgisCtrl import QgisCtrl
#from Ferramentas_Producao.modules.rasterMetadata.models.filters import Filters
from Ferramentas_Producao.modules.rasterMetadata.factories.widgetFactory import WidgetFactory
from Ferramentas_Producao.modules.rasterMetadata.models.rasterMetadata import RasterMetadata

class RasterMetadataCtrl:
    
    def __init__(
            self,
            RasterMetadata=RasterMetadata,
            widgetFactory=WidgetFactory(),
            qgis=QgisCtrl()
        ):
        self.widgetFactory = widgetFactory
        self.qgis = qgis
        self.rasterMetadata = RasterMetadata(self)
        self.dlg = None
        self.enabled = False

    def connectQgisSignals(self):
        self.qgis.on('LayersAdded', self.layersAdded)

    def disconnectQgisSignals(self):
        self.qgis.off('LayersAdded', self.layersAdded)

    def setEnabled(self, b):
        self.enabled = b
        if  self.enabled:
            self.connectQgisSignals()
            self.rasterMetadata.setLayers(self.qgis.getLoadedVectorLayers())
            self.rasterMetadata.connectLayersSignal()
        else:
            self.disconnectQgisSignals()
            self.rasterMetadata.setLayers([])
            self.rasterMetadata.disconnectLayersSignal()

    def isEnabled(self):
        return self.enabled

    def openDialog(self):
        if self.dlg:
            self.dlg.close()
        self.dlg = self.widgetFactory.createWidget('RasterMetadataDlg', self)
        self.dlg.setConfig(
            self.rasterMetadata.getConfigText()
        )
        self.dlg.show()

    def setConfig(self, data):
        self.rasterMetadata.setConfig(data)

    def layersAdded(self, newLayers):
        self.rasterMetadata.setLayers(self.qgis.getLoadedVectorLayers())
        self.rasterMetadata.disconnectLayersSignal()
        self.rasterMetadata.connectLayersSignal()

    def getActiveVectorLayer(self):
        return self.qgis.getActiveVectorLayer()

    def getVisibleRasters(self):
        return self.qgis.getVisibleRasters()

    def canvasRefresh(self):
        self.qgis.canvasRefresh()
        
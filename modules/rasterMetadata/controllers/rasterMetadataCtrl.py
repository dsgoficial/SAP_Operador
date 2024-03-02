from SAP_Operador.modules.qgis.qgisApi import QgisApi
from SAP_Operador.modules.rasterMetadata.factories.widgetFactory import WidgetFactory
from SAP_Operador.modules.rasterMetadata.models.rasterMetadata import RasterMetadata
from SAP_Operador.modules.utils.factories.utilsFactory import UtilsFactory

class RasterMetadataCtrl:
    
    def __init__(
            self,
            rasterMetadata=None,
            widgetFactory=None,
            qgis=None,
            messageFactory=None,
        ):
        self.widgetFactory = WidgetFactory() if widgetFactory is None else widgetFactory
        self.qgis = QgisApi() if qgis is None else qgis
        self.rasterMetadata = RasterMetadata(self) if rasterMetadata is None else rasterMetadata
        self.dlg = None
        self.enabled = False
        self.messageFactory = UtilsFactory().createMessageFactory() if messageFactory is None else messageFactory
    
    def showErrorMessageBox(self, message):
        messageDlg = self.messageFactory.createMessage('ErrorMessageBox')
        messageDlg.show(self.qgis.getMainWindow(), 'Erro', message)

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
            self.rasterMetadata.disconnectLayersSignal()
            self.rasterMetadata.setLayers([])

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
        
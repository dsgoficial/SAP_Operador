from SAP_Operador.modules.qgis.qgisApi import QgisApi
from SAP_Operador.modules.combinationViewer.models.filters import Filters
from SAP_Operador.modules.combinationViewer.factories.widgetFactory import WidgetFactory

class CombinationViewerCtrl:
    
    def __init__(
            self,
            widgetFactory=None,
            qgis=None,
            filters=None,
        ):
        self.widgetFactory = WidgetFactory() if widgetFactory is None else widgetFactory
        self.qgis = QgisApi() if qgis is None else qgis
        self.filters = Filters() if filters is None else filters
        self.dlg = None
        self.qgis.on('LayersAdded', self.refreshDialog)

    def openDialog(self):
        if self.dlg:
            self.dlg.close()
        self.dlg = self.widgetFactory.createWidget('CombinationViewerDlg', self)
        self.dlg.loadLayerNames(
            self.getLoadedVectorLayerNames()
        )
        self.dlg.show()

    def refreshDialog(self, layers):
        pass

    def getLoadedVectorLayers(self):
        return self.qgis.getLoadedVectorLayers()

    def getLoadedVectorLayerNames(self):
        return [l.name() for l in self.getLoadedVectorLayers() ]

    def filterCommonFields(self, selectedLayerNames):
        selectedLayers = [l for l in self.getLoadedVectorLayers() if l.name() in selectedLayerNames]
        return self.filters.filterCommonFields(selectedLayers)

    def filterAttributeCombination(self, selectedFields, selectedLayerNames):
        selectedLayers = [l for l in self.getLoadedVectorLayers() if l.name() in selectedLayerNames]
        return self.filters.filterAttributeCombination(selectedFields, selectedLayers)

    def getLayersByAttributes(self, selectedAttributes, selectedLayerNames):
        selectedLayers = [l for l in self.getLoadedVectorLayers() if l.name() in selectedLayerNames]
        return self.filters.getLayersByAttributes(selectedAttributes, selectedLayers)
        
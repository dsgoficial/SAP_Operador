from Ferramentas_Producao.modules.qgis.qgisCtrl import QgisCtrl
from Ferramentas_Producao.modules.qgis.qgisCtrl import QgisCtrl
from Ferramentas_Producao.modules.combinationViewer.models.filters import Filters
from Ferramentas_Producao.modules.combinationViewer.factories.widgetFactory import WidgetFactory

class CombinationViewerCtrl:
    
    def __init__(
            self,
            widgetFactory=WidgetFactory(),
            qgis=QgisCtrl(),
            filters=Filters()
        ):
        self.widgetFactory = widgetFactory
        self.qgis = qgis
        self.filters = filters
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
        
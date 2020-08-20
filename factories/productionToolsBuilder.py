from PyQt5 import QtCore

from Ferramentas_Producao.interfaces.IProductionToolsBuilder import IProductionToolsBuilder

from Ferramentas_Producao.widgets.productionToolsDock import ProductionToolsDock

class ProductionToolsBuilder(IProductionToolsBuilder):

    def __init__(self):
        super(ProductionToolsBuilder, self).__init__()
        self.reset()

    def reset(self):
        self.obj = ProductionToolsDock()

    def addActivityWidget(self, name, widget):
        self.obj.addActivityWidget(name, widget)
    
    def addLineageLabel(self, lineage):
        self.obj.addLineageLabel(lineage)

    def getResult(self):
        obj = self.obj
        self.reset()
        return obj
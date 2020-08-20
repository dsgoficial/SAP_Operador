from Ferramentas_Producao.interfaces.IGUIFactory import IGUIFactory
from Ferramentas_Producao.factories.productionToolsDirector import ProductionToolsDirector
from Ferramentas_Producao.factories.productionToolsBuilder import ProductionToolsBuilder
from Ferramentas_Producao.widgets.routinesDialog import RoutinesDialog

class GUIFactory(IGUIFactory):
    
    def __init__(self):
        super(GUIFactory, self).__init__()

    def makeProductionToolsDock(self, mediator):
        director = ProductionToolsDirector()
        builder = ProductionToolsBuilder()
        director.constructProductionToolsDock( builder, mediator )
        return builder.getResult()

    def makeRoutinesDialog(self, mediator, parent):
        return RoutinesDialog(mediator, parent)
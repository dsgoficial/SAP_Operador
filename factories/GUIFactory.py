from Ferramentas_Producao.interfaces.IGUIFactory import IGUIFactory
from Ferramentas_Producao.factories.productionToolsDirector import ProductionToolsDirector
from Ferramentas_Producao.factories.productionToolsBuilder import ProductionToolsBuilder
from Ferramentas_Producao.widgets.routinesDialog import RoutinesDialog
from Ferramentas_Producao.widgets.activityDataSummary import ActivityDataSummary

class GUIFactory(IGUIFactory):
    
    def __init__(self):
        super(GUIFactory, self).__init__()

    def makeProductionToolsDock(self, mediator, obj=None):
        director = ProductionToolsDirector()
        builder = ProductionToolsBuilder()
        if obj is not None:
            obj.removeAllWidgets()
            builder.setObject(obj)
        director.constructProductionToolsDock( builder, mediator )
        return builder.getResult()

    def makeActivitySummaryDialog(self, mediator, layerNames, ruleNames):
        dialog = ActivityDataSummary(mediator)
        dialog.setLayerNames('Camadas:', layerNames)
        dialog.setRuleNames('Regras:', ruleNames)
        dialog.adjustWidgets()
        return dialog

    def makeRoutinesDialog(self, mediator, parent):
        return RoutinesDialog(mediator, parent)
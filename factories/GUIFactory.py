from SAP_Operador.interfaces.IGUIFactory import IGUIFactory
from SAP_Operador.factories.productionToolsDirector import ProductionToolsDirector
from SAP_Operador.factories.productionToolsBuilder import ProductionToolsBuilder
from SAP_Operador.widgets.routinesDialog import RoutinesDialog
from SAP_Operador.widgets.activityDataSummary import ActivityDataSummary
from SAP_Operador.factories.changeStylesSingleton import ChangeStylesSingleton

class GUIFactory(IGUIFactory):
    
    def __init__(self):
        super(GUIFactory, self).__init__()

    def makeRemoteProductionToolsDock(self, controller, sap, obj=None):
        director = ProductionToolsDirector()
        builder = ProductionToolsBuilder()
        if obj is not None:
            obj.removeAllWidgets()
            builder.setObject(obj)
        director.constructRemoteProductionToolsDock( builder, controller, sap )
        return builder.getResult()

    def makeLocalProductionToolsDock(self, controller, obj=None):
        director = ProductionToolsDirector()
        builder = ProductionToolsBuilder()
        if obj is not None:
            obj.removeAllWidgets()
            builder.setObject(obj)
        director.constructLocalProductionToolsDock( builder, controller )
        return builder.getResult()

    def makeActivitySummaryDialog(self, controller, layerNames, ruleNames):
        dialog = ActivityDataSummary(controller)
        dialog.setLayerNames('Camadas:', layerNames)
        dialog.setRuleNames('Regras:', ruleNames)
        dialog.adjustWidgets()
        return dialog

    def makeRoutinesDialog(self, controller, parent):
        return RoutinesDialog(controller, parent)

    def getWidget(self, name, controller):
        widgets = {
            'ChangeStyleWidget': lambda: ChangeStylesSingleton.getInstance(controller),
        }
        return widgets[name]() if name in widgets else None
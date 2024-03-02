from SAP_Operador.interfaces.IActivityWidgetFactory import IActivityWidgetFactory
from SAP_Operador.factories.activityWidgetDirector import ActivityWidgetDirector
from SAP_Operador.factories.activityInfoWidgetBuilder import ActivityInfoWidgetBuilder
from SAP_Operador.factories.activityDataWidgetBuilder import ActivityDataWidgetBuilder
from SAP_Operador.factories.activityInputsWidgetBuilder import ActivityInputsWidgetBuilder
from SAP_Operador.factories.activityInputLinksWidgetBuilder import ActivityInputLinksWidgetBuilder
from SAP_Operador.factories.activityRoutinesWidgetBuilder import ActivityRoutinesWidgetBuilder
from SAP_Operador.factories.loadLocalActivityWidgetBuilder import LoadLocalActivityWidgetBuilder

class ActivityWidgetFactory(IActivityWidgetFactory):
    
    def __init__(self):
        super(ActivityWidgetFactory, self).__init__()

    def makeActivityInfoWidget(self, controller):
        director = ActivityWidgetDirector()
        builder = ActivityInfoWidgetBuilder()
        director.constructActivityInfoWidget( builder, controller )
        return builder.getResult()

    def makeActivityDataWidget(self, controller, sap):
        director = ActivityWidgetDirector()
        builder = ActivityDataWidgetBuilder()
        director.constructActivityDataWidget( builder, controller, sap )
        result = builder.getResult()
        result.setSap(sap)
        return result

    def makeActivityInputsWidget(self, controller):
        director = ActivityWidgetDirector()
        builder = ActivityInputsWidgetBuilder()
        director.constructActivityInputsWidget( builder, controller )
        return builder.getResult()

    def makeActivityInputLinksWidget(self, controller):
        director = ActivityWidgetDirector()
        builder = ActivityInputLinksWidgetBuilder()
        director.constructActivityInputLinksWidget( builder, controller )
        return builder.getResult()

    def makeActivityRoutinesWidget(self, controller):
        director = ActivityWidgetDirector()
        builder = ActivityRoutinesWidgetBuilder()
        director.constructActivityRoutinesWidget( builder, controller )
        return builder.getResult()

    def makeLoadLocalActivityWidget(self, controller):
        director = ActivityWidgetDirector()
        builder = LoadLocalActivityWidgetBuilder()
        director.constructLoadLocalActivityWidgetBuilder( builder, controller )
        return builder.getResult()
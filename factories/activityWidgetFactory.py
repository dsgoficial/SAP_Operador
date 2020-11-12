from Ferramentas_Producao.interfaces.IActivityWidgetFactory import IActivityWidgetFactory
from Ferramentas_Producao.factories.activityWidgetDirector import ActivityWidgetDirector
from Ferramentas_Producao.factories.activityInfoWidgetBuilder import ActivityInfoWidgetBuilder
from Ferramentas_Producao.factories.activityDataWidgetBuilder import ActivityDataWidgetBuilder
from Ferramentas_Producao.factories.activityInputsWidgetBuilder import ActivityInputsWidgetBuilder
from Ferramentas_Producao.factories.activityInputLinksWidgetBuilder import ActivityInputLinksWidgetBuilder
from Ferramentas_Producao.factories.activityRoutinesWidgetBuilder import ActivityRoutinesWidgetBuilder
from Ferramentas_Producao.factories.loadLocalActivityWidgetBuilder import LoadLocalActivityWidgetBuilder

class ActivityWidgetFactory(IActivityWidgetFactory):
    
    def __init__(self):
        super(ActivityWidgetFactory, self).__init__()

    def makeActivityInfoWidget(self, controller):
        director = ActivityWidgetDirector()
        builder = ActivityInfoWidgetBuilder()
        director.constructActivityInfoWidget( builder, controller )
        return builder.getResult()

    def makeActivityDataWidget(self, controller):
        director = ActivityWidgetDirector()
        builder = ActivityDataWidgetBuilder()
        director.constructActivityDataWidget( builder, controller )
        return builder.getResult()

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
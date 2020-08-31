from Ferramentas_Producao.interfaces.IActivityWidgetFactory import IActivityWidgetFactory
from Ferramentas_Producao.factories.activityWidgetDirector import ActivityWidgetDirector
from Ferramentas_Producao.factories.activityInfoWidgetBuilder import ActivityInfoWidgetBuilder
from Ferramentas_Producao.factories.activityDataWidgetBuilder import ActivityDataWidgetBuilder
from Ferramentas_Producao.factories.activityInputsWidgetBuilder import ActivityInputsWidgetBuilder
from Ferramentas_Producao.factories.activityInputLinksWidgetBuilder import ActivityInputLinksWidgetBuilder

from Ferramentas_Producao.factories.activityRoutinesWidgetBuilder import ActivityRoutinesWidgetBuilder

class ActivityWidgetFactory(IActivityWidgetFactory):
    
    def __init__(self):
        super(ActivityWidgetFactory, self).__init__()

    def makeActivityInfoWidget(self, mediator):
        director = ActivityWidgetDirector()
        builder = ActivityInfoWidgetBuilder()
        director.constructActivityInfoWidget( builder, mediator )
        return builder.getResult()

    def makeActivityDataWidget(self, mediator):
        director = ActivityWidgetDirector()
        builder = ActivityDataWidgetBuilder()
        director.constructActivityDataWidget( builder, mediator )
        return builder.getResult()

    def makeActivityInputsWidget(self, mediator):
        director = ActivityWidgetDirector()
        builder = ActivityInputsWidgetBuilder()
        director.constructActivityInputsWidget( builder, mediator )
        return builder.getResult()

    def makeActivityInputLinksWidget(self, mediator):
        director = ActivityWidgetDirector()
        builder = ActivityInputLinksWidgetBuilder()
        director.constructActivityInputLinksWidget( builder, mediator )
        return builder.getResult()

    def makeActivityRoutinesWidget(self, mediator):
        director = ActivityWidgetDirector()
        builder = ActivityRoutinesWidgetBuilder()
        director.constructActivityRoutinesWidget( builder, mediator )
        return builder.getResult()
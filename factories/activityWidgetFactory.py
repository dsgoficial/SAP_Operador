from Ferramentas_Producao.interfaces.IActivityWidgetFactory import IActivityWidgetFactory
from Ferramentas_Producao.factories.activityWidgetDirector import ActivityWidgetDirector
from Ferramentas_Producao.factories.activityInfoWidgetBuilder import ActivityInfoWidgetBuilder
from Ferramentas_Producao.factories.activityDataWidgetBuilder import ActivityDataWidgetBuilder
from Ferramentas_Producao.widgets.activityRoutines import ActivityRoutines

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

    def makeActivityRoutinesWidget(self, mediator):
        return ActivityRoutines(mediator)
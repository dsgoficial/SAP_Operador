from Ferramentas_Producao.factories.activityWidgetFactory import ActivityWidgetFactory

class ProductionToolsDirector:

    def __init__(self, 
            activityWidgetFactory=ActivityWidgetFactory()  
        ):
        self.activityWidgetFactory = activityWidgetFactory

    def constructProductionToolsDock(self, builder, mediator):
        for widget in [
                {
                    'name': 'Atividade:',
                    'widget': self.activityWidgetFactory.makeActivityInfoWidget(mediator=mediator)
                },
                {
                    'name': 'Dados:',
                    'widget': self.activityWidgetFactory.makeActivityDataWidget(mediator=mediator)
                },
                {
                    'name': 'Rotinas:',
                    'widget': self.activityWidgetFactory.makeActivityRoutinesWidget(mediator=mediator)
                }
               
            ]:
            builder.addActivityWidget(widget['name'], widget['widget'])
        for lineage in mediator.getActivityLineage():
            builder.addLineageLabel(lineage)
from Ferramentas_Producao.factories.activityWidgetFactory import ActivityWidgetFactory

class ProductionToolsDirector:

    def __init__(self, 
            activityWidgetFactory=ActivityWidgetFactory()  
        ):
        self.activityWidgetFactory = activityWidgetFactory

    def constructProductionToolsDock(self, builder, mediator):
        widgets = [
            {
                'name': 'Atividade:',
                'widget': self.activityWidgetFactory.makeActivityInfoWidget(mediator=mediator)
            },
            {
                'name': 'Dados:',
                'widget': self.activityWidgetFactory.makeActivityDataWidget(mediator=mediator)
            },
            {
                'name': 'Insumos:',
                'widget': self.activityWidgetFactory.makeActivityInputsWidget(mediator=mediator)
            },
            {
                'name': 'Insumos(2):',
                'widget': self.activityWidgetFactory.makeActivityInputLinksWidget(mediator=mediator)
            },
            {
                'name': 'Rotinas:',
                'widget': self.activityWidgetFactory.makeActivityRoutinesWidget(mediator=mediator)
            }
            
        ]
        for i, widget in enumerate(widgets):
            builder.addActivityWidget(widget['name'], widget['widget'])
            if not(i == (len(widgets) - 1)):
                builder.addLine()
        for lineage in mediator.getActivityLineage():
            builder.addLineageLabel(lineage)
        builder.setShortcutDescription(mediator.getShortcutQgisDescription())
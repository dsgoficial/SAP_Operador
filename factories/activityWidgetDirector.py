from Ferramentas_Producao.widgets.activityData import ActivityData

class ActivityWidgetDirector:

    def constructActivityInfoWidget(self, builder, mediator):
        builder.setMediator(mediator)
        builder.setDescription( "Descrição:", mediator.getActivityDescription())
        builder.setNotes( "Observações:", mediator.getActivityNotes() )
        builder.setRequirements( "Requisitos:", mediator.getActivityRequirements() )
        builder.setButtons()

    def constructActivityDataWidget(self, builder, mediator):
        builder.setMediator(mediator)
        builder.setStyles(mediator.getActivityStyles())
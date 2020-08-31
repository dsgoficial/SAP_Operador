from Ferramentas_Producao.widgets.activityData import ActivityData

class ActivityWidgetDirector:

    def constructActivityInfoWidget(self, builder, mediator):
        builder.setMediator(mediator)
        builder.setDescription( "Descrição:", mediator.getActivityDescription())
        builder.setEPSG('EPSG:', mediator.getActivityEPSG())
        builder.setNotes( "Observações:", mediator.getActivityNotes() )
        builder.setRequirements( "Requisitos:", mediator.getActivityRequirements() )
        builder.setButtons()

    def constructActivityDataWidget(self, builder, mediator):
        builder.setMediator(mediator)
        builder.setStyles(mediator.getActivityStyles())

    def constructActivityInputsWidget(self, builder, mediator):
        builder.setMediator(mediator)
        builder.setInputs([ 
            data for data in mediator.getActivityInputs()
            if not(data['tipo_insumo_id'] in [4,5])
        ])
        builder.adjustWidgets()

    def constructActivityInputLinksWidget(self, builder, mediator):
        builder.setMediator(mediator)
        builder.setInputs([ 
            data for data in mediator.getActivityInputs()
            if data['tipo_insumo_id'] in [4,5]
        ])
        builder.adjustWidgets()

    def constructActivityRoutinesWidget(self, builder, mediator):
        builder.setMediator(mediator)
        builder.setRoutines(mediator.getActivityRoutines())
        builder.adjustWidgets()
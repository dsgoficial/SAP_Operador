from Ferramentas_Producao.widgets.selectItems import SelectItems

class ActivityWidgetDirector:

    def constructActivityInfoWidget(self, builder, controller):
        builder.setController(controller)
        builder.setDescription( "Descrição:", controller.getActivityDescription())
        builder.addObservation('Projeto:', controller.getProject())
        builder.addObservation('Lote:', controller.getLot())
        builder.addObservation('Escala:', controller.getScale())
        builder.addObservation('EPSG:', controller.getActivityEPSG())
        builder.setNotes( "Observações:", controller.getActivityNotes() )
        builder.setRequirements( "Requisitos:", controller.getActivityRequirements() )
        builder.setButtons()

    def constructActivityDataWidget(self, builder, controller):
        builder.enabledMenuButton( len( controller.getSapMenus() ) > 0 )
        builder.setController(controller)

    def constructActivityInputsWidget(self, builder, controller):
        builder.setController(controller)
        builder.setInputs([ 
            data for data in controller.getActivityInputs()
            if not(data['tipo_insumo_id'] in [4,5])
        ])
        builder.adjustWidgets()

    def constructActivityInputLinksWidget(self, builder, controller):
        builder.setController(controller)
        builder.setInputs([ 
            data for data in controller.getActivityInputs()
            if data['tipo_insumo_id'] in [4,5]
        ])
        builder.adjustWidgets()

    def constructActivityRoutinesWidget(self, builder, controller):
        builder.setController(controller)
        builder.setRoutines(controller.getActivityRoutines())
        builder.adjustWidgets()

    def constructLoadLocalActivityWidgetBuilder(self, builder, controller):
        builder.setController(controller)
        
        workspacesSelectItems = SelectItems('Áreas de trabalho:')
        workspacesSelectItems.addItems(controller.getActivityWorkspaces())

        layersSelectItems = SelectItems('Camadas:')
        layersSelectItems.addItems(controller.getActivityLayers())

        builder.setStyleNames(controller.getActivityStyles())
        builder.setWorkspaceSelectItems(workspacesSelectItems)
        builder.setLayersSelectItems(layersSelectItems)
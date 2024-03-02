from SAP_Operador.factories.activityWidgetFactory import ActivityWidgetFactory
from SAP_Operador.widgets.localController import LocalController

class ProductionToolsDirector:

    def __init__(self, 
            activityWidgetFactory=None,
        ):
        self.activityWidgetFactory = ActivityWidgetFactory() if activityWidgetFactory is None else activityWidgetFactory

    def constructRemoteProductionToolsDock(self, builder, controller, sap):
        builder.setController(controller)
        widgets = [
            {
                'name': 'Atividade:',
                'widget': self.activityWidgetFactory.makeActivityInfoWidget(controller=controller)
            },
            {
                'name': 'Dados:',
                'widget': self.activityWidgetFactory.makeActivityDataWidget(controller=controller, sap=sap)
            },
            {
                'name': 'Insumos:',
                'widget': self.activityWidgetFactory.makeActivityInputsWidget(controller=controller)
            },
            {
                'name': 'Insumos(2):',
                'widget': self.activityWidgetFactory.makeActivityInputLinksWidget(controller=controller)
            },
            {
                'name': 'Rotinas:',
                'widget': self.activityWidgetFactory.makeActivityRoutinesWidget(controller=controller)
            }
            
        ]
        for i, widget in enumerate(reversed(widgets)):
            if not widget['widget'].hasData():
                continue
            builder.addActivityWidget(widget['name'], widget['widget'])
            if not(i == (len(widgets) - 1)):
                builder.addLine()
        for lineage in controller.getActivityLineage():
            builder.addLineageLabel(lineage)
        builder.setShortcutDescription(controller.getShortcutQgisDescription())
        builder.addPomodoro(controller.getPomodoroWidget())

    def constructLocalProductionToolsDock(self, builder, controller):
        builder.setController(controller)
        activityInfo = self.activityWidgetFactory.makeActivityInfoWidget(controller=controller)
        activityInfo.hideButtons(True)
        widgets = [
            {
                'name': 'Atividade:',
                'widget': activityInfo
            },
            {
                'name': 'Controle:',
                'widget': LocalController(controller=controller)
            },
            {
                'name': 'Dados:',
                'widget': self.activityWidgetFactory.makeActivityDataWidget(controller=controller)
            },
            {
                'name': 'Insumos:',
                'widget': self.activityWidgetFactory.makeActivityInputsWidget(controller=controller)
            },
            {
                'name': 'Insumos(2):',
                'widget': self.activityWidgetFactory.makeActivityInputLinksWidget(controller=controller)
            },
            {
                'name': 'Rotinas:',
                'widget': self.activityWidgetFactory.makeActivityRoutinesWidget(controller=controller)
            }
            
        ]
        for i, widget in enumerate(reversed(widgets)):
            if not widget['widget'].hasData():
                continue
            builder.addActivityWidget(widget['name'], widget['widget'])
            if not(i == (len(widgets) - 1)):
                builder.addLine()
        for lineage in controller.getActivityLineage():
            builder.addLineageLabel(lineage)
        builder.setShortcutDescription(controller.getShortcutQgisDescription())
        builder.addPomodoro(controller.getPomodoroWidget())
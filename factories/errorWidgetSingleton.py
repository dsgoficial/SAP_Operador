from Ferramentas_Producao.widgets.errorWidget  import ErrorWidget

class ErrorWidgetSingleton:

    widget = None

    @staticmethod
    def getInstance(controller):
        if not ErrorWidgetSingleton.widget:
            ErrorWidgetSingleton.widget = ErrorWidget(controller)
        return ErrorWidgetSingleton.widget
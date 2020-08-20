from Ferramentas_Producao.modules.sap.widgets.reportErrorDialog import ReportErrorDialog

class ReportErrorDialogSingleton:

    dialog = None

    @staticmethod
    def getInstance(mediator):
        if not ReportErrorDialogSingleton.dialog:
            ReportErrorDialogSingleton.dialog = ReportErrorDialog(mediator)
        return ReportErrorDialogSingleton.dialog
from Ferramentas_Producao.modules.sap.widgets.reportErrorDialog import ReportErrorDialog

class ReportErrorDialogSingleton:

    dialog = None

    @staticmethod
    def getInstance(controller):
        if not ReportErrorDialogSingleton.dialog:
            ReportErrorDialogSingleton.dialog = ReportErrorDialog(controller)
        return ReportErrorDialogSingleton.dialog
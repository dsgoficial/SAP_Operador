from SAP_Operador.modules.sap.widgets.reportErrorDialog import ReportErrorDialog

class ReportErrorDialogSingleton:

    dialog = None

    @staticmethod
    def getInstance(controller, qgis):
        if not ReportErrorDialogSingleton.dialog:
            ReportErrorDialogSingleton.dialog = ReportErrorDialog(controller, qgis)
        return ReportErrorDialogSingleton.dialog
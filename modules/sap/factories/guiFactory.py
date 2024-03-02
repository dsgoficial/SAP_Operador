
from SAP_Operador.modules.sap.factories.endActivityDialogSingleton import EndActivityDialogSingleton
from SAP_Operador.modules.sap.widgets.reportErrorDialog import ReportErrorDialog

class GUIFactory:

    def createReportErrorDialog(self, controller, qgis):
        return ReportErrorDialog(controller, qgis)

    def createEndActivityDialog(self, controller, activeObs):
        return EndActivityDialogSingleton.getInstance(controller, activeObs)

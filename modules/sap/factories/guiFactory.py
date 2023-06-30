
from Ferramentas_Producao.modules.sap.factories.endActivityDialogSingleton import EndActivityDialogSingleton
from Ferramentas_Producao.modules.sap.widgets.reportErrorDialog import ReportErrorDialog

class GUIFactory:

    def createReportErrorDialog(self, controller, qgis):
        return ReportErrorDialog(controller, qgis)

    def createEndActivityDialog(self, controller):
        return EndActivityDialogSingleton.getInstance(controller)

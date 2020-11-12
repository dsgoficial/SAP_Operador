
from Ferramentas_Producao.modules.sap.factories.endActivityDialogSingleton import EndActivityDialogSingleton
from Ferramentas_Producao.modules.sap.factories.reportErrorDialogSingleton import ReportErrorDialogSingleton

class GUIFactory:

    def createReportErrorDialog(self, controller):
        return ReportErrorDialogSingleton.getInstance(controller)

    def createEndActivityDialog(self, controller):
        return EndActivityDialogSingleton.getInstance(controller)

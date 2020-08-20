
from Ferramentas_Producao.modules.sap.factories.loginSingleton import LoginSingleton
from Ferramentas_Producao.modules.sap.factories.endActivityDialogSingleton import EndActivityDialogSingleton
from Ferramentas_Producao.modules.sap.factories.reportErrorDialogSingleton import ReportErrorDialogSingleton

class GUIFactory:

    def createReportErrorDialog(self, mediator):
        return ReportErrorDialogSingleton.getInstance(mediator)

    def createEndActivityDialog(self, mediator):
        return EndActivityDialogSingleton.getInstance(mediator)

    def createLoginDialog(self, mediator):
        return LoginSingleton.getInstance()

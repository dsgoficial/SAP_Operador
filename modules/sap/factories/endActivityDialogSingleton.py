from Ferramentas_Producao.modules.sap.widgets.endActivityDialog import EndActivityDialog

class EndActivityDialogSingleton:

    dialog = None

    @staticmethod
    def getInstance(mediator):
        if not EndActivityDialogSingleton.dialog:
            EndActivityDialogSingleton.dialog = EndActivityDialog(mediator)
        return EndActivityDialogSingleton.dialog
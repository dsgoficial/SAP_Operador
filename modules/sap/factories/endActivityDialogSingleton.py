from Ferramentas_Producao.modules.sap.widgets.endActivityDialog import EndActivityDialog

class EndActivityDialogSingleton:

    dialog = None

    @staticmethod
    def getInstance(controller):
        if not EndActivityDialogSingleton.dialog:
            EndActivityDialogSingleton.dialog = EndActivityDialog(controller)
        return EndActivityDialogSingleton.dialog
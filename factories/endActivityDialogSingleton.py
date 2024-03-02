from SAP_Operador.widgets.endActivityDialog import EndActivityDialog

class EndActivityDialogSingleton:

    dialog = None

    @staticmethod
    def getInstance():
        if not EndActivityDialogSingleton.dialog:
            EndActivityDialogSingleton.dialog = EndActivityDialog()
        return EndActivityDialogSingleton.dialog
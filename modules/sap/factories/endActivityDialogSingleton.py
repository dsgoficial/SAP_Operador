from SAP_Operador.modules.sap.widgets.endActivityDialog import EndActivityDialog

class EndActivityDialogSingleton:

    dialog = None

    @staticmethod
    def getInstance(*args):
        if not EndActivityDialogSingleton.dialog:
            EndActivityDialogSingleton.dialog = EndActivityDialog(*args)
        return EndActivityDialogSingleton.dialog
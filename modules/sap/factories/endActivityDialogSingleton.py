from SAP_Operador.modules.sap.widgets.endActivityDialog import EndActivityDialog

class EndActivityDialogSingleton:

    dialog = None

    @staticmethod
    def getInstance(*args):
        if EndActivityDialogSingleton.dialog:
            EndActivityDialogSingleton.dialog.close()
            EndActivityDialogSingleton.dialog = None
        EndActivityDialogSingleton.dialog = EndActivityDialog(*args)
        return EndActivityDialogSingleton.dialog
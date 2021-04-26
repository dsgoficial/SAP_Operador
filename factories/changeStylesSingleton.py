from Ferramentas_Producao.widgets.changeStyles  import ChangeStyles

class ChangeStylesSingleton:

    widget = None

    @staticmethod
    def getInstance(controller):
        if not ChangeStylesSingleton.widget:
            ChangeStylesSingleton.widget = ChangeStyles(controller)
        return ChangeStylesSingleton.widget
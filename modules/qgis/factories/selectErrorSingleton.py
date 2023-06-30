from Ferramentas_Producao.modules.qgis.mapTools.selectError import SelectError

class SelectErrorSingleton:

    tool = None

    @staticmethod
    def getInstance():
        if not SelectErrorSingleton.tool:
            SelectErrorSingleton.tool = SelectError()
        return SelectErrorSingleton.tool
from SAP_Operador.modules.qgis.mapTools.trimLine import TrimLine

class TrimLineMapToolSingleton:

    tool = None

    @staticmethod
    def getInstance():
        if not TrimLineMapToolSingleton.tool:
            TrimLineMapToolSingleton.tool = TrimLine()
        return TrimLineMapToolSingleton.tool
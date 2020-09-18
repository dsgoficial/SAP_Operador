from Ferramentas_Producao.modules.qgis.mapTools.expandLine import ExpandLine

class ExpandLineMapToolSingleton:

    tool = None

    @staticmethod
    def getInstance():
        if not ExpandLineMapToolSingleton.tool:
            ExpandLineMapToolSingleton.tool = ExpandLine()
        return ExpandLineMapToolSingleton.tool
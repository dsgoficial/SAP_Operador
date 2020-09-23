from Ferramentas_Producao.modules.qgis.mapTools.convergencePoint import ConvergencePoint

class ConvergencePointMapToolSingleton:

    tool = None

    @staticmethod
    def getInstance():
        if not ConvergencePointMapToolSingleton.tool:
            ConvergencePointMapToolSingleton.tool = ConvergencePoint()
        return ConvergencePointMapToolSingleton.tool
from qgis.core import QgsProject
from qgis.utils import iface


class ThemeCycle:

    def __init__(self):
        self._current_idx = -1

    def cycle(self):
        themes = QgsProject.instance().mapThemeCollection().mapThemes()
        if not themes:
            iface.messageBar().pushWarning("Map Themes", "Nenhum Map Theme encontrado no projeto.")
            return
        self._current_idx = (self._current_idx + 1) % len(themes)
        next_theme = themes[self._current_idx]
        collection = QgsProject.instance().mapThemeCollection()
        root = QgsProject.instance().layerTreeRoot()
        collection.applyTheme(next_theme, root, iface.layerTreeView().layerTreeModel())
        iface.messageBar().pushSuccess(
            "Map Theme",
            f"[{self._current_idx + 1}/{len(themes)}]  {next_theme}",
        )

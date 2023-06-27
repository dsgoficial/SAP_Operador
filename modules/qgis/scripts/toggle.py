from qgis.core import QgsProject
from qgis.utils import iface

def toggle(styleLabel, startBool):
    project = QgsProject.instance()
    layers = project.mapLayers().values()
    for layer in layers:
        sym_rend = layer.renderer()
        lgd_syms = sym_rend.legendSymbolItems()
        for lgd_sym in lgd_syms:
            lbl = lgd_sym.label()
            if lbl == styleLabel:
                key = lgd_sym.ruleKey()
                sym_rend.checkLegendSymbolItem(key, startBool)
    iface.mapCanvas().refreshAllLayers()
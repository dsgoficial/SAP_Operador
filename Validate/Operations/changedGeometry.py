# -*- coding: utf-8 -*-

import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from Ferramentas_Producao.utils import msgBox

class ChangedGeometry(QtCore.QObject):
    def __init__(self, iface):
        super(ChangedGeometry, self).__init__()
        self.iface = iface

    def validate(self):
        layer = self.iface.activeLayer()
        if layer and layer.type() == core.QgsMapLayer.VectorLayer:
            changed_geometries = layer.editBuffer().changedGeometries() if layer.editBuffer() else ''
            self.check_changed_geometry(changed_geometries) if changed_geometries else ''

    def check_changed_geometry(self, changed_geometries):
        layer = self.iface.activeLayer()
        variable_name = u'area_trabalho_poligono'
        ewkt = core.QgsExpressionContextUtils.layerScope(layer).variable(
            variable_name
        )
        if ewkt:
            wkt = ewkt.split(';')[1]
            geom = core.QgsGeometry.fromWkt(wkt)
            feat_key = sorted(list(changed_geometries.keys()))[0]
            feat_geom = changed_geometries[feat_key]
            if geom.intersects(feat_geom) == False:
                html = u'''<p style="color:red">
                            A edição da camada "{}" está fora da moldura!
                        </p>'''.format(layer.name())
                msgBox.show(text=html, title=u"critical")
                layer.undoStack().undo()
                self.iface.mapCanvas().refresh()

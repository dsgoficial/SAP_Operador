# -*- coding: utf-8 -*-

import os, sys
from PyQt5 import QtCore
from qgis import core, gui
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox

class AddFeatures(QtCore.QObject):
    def __init__(self, iface):
        super(AddFeatures, self).__init__()
        self.iface = iface

    def validate(self):
        layer = self.iface.activeLayer()
        if layer:
            features_added = layer.editBuffer().addedFeatures() if layer.editBuffer() else ''
            self.check_add_feature(features_added) if features_added else ''

    def check_add_feature(self, features_added):
        layer = self.iface.activeLayer()
        variable_name = u'area_trabalho_poligono'
        ewkt = core.QgsExpressionContextUtils.layerScope(layer).variable(
            variable_name
        )
        if ewkt:
            wkt = ewkt.split(';')[1]
            geom = core.QgsGeometry.fromWkt(wkt)
            feat_key = sorted(list(features_added.keys()))[0]
            feat = features_added[feat_key]
            if geom.intersects(feat.geometry()) == False:
                html = u'''<p style="color:red">
                            A aquisição da camada "{}" está fora da moldura!
                        </p>'''.format(layer.name())
                msgBox.show(text=html, title=u"critical")
                layer.undoStack().undo()
            self.iface.mapCanvas().refresh()

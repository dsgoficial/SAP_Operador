# -*- coding: utf-8 -*-

import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from Ferramentas_Producao.utils import msgBox

class DelFeatures(QtCore.QObject):
    def __init__(self, iface):
        super(DelFeatures, self).__init__()
        self.iface = iface

    def validate(self):
        layer = self.iface.activeLayer()
        if layer and layer.type() == core.QgsMapLayer.VectorLayer:
            features_deleted_ids = layer.editBuffer().deletedFeatureIds() if layer.editBuffer() else ''
            self.check_del_feature(features_deleted_ids) if features_deleted_ids else ''
                

    def check_del_feature(self, features_deleted_ids):
        layer = self.iface.activeLayer()
        variable_name = u'area_trabalho_poligono'
        ewkt = core.QgsExpressionContextUtils.layerScope(layer).variable(
            variable_name
        )
        if ewkt:
            wkt = ewkt.split(';')[1]
            geom_poly = core.QgsGeometry.fromWkt(wkt)
            feats_requests = [ core.QgsFeatureRequest(i) for i in  features_deleted_ids ]
            check_intersects = False
            for feat_req in feats_requests:
                for feat in layer.dataProvider().getFeatures(feat_req):
                    if geom_poly.buffer(0.1,1).contains(feat.geometry()):
                        check_intersects = True
            if check_intersects:
                html = u'''<p style="color:red">
                            Não é permitido deletar feições que intersectam a moldura.
                        </p>'''.format(layer.name())
                msgBox.show(text=html, title=u"critical")
                if layer.undoStack().canUndo():
                    layer.undoStack().undo()
                self.iface.mapCanvas().refresh()

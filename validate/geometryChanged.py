# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui, utils
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from managerQgis.projectQgis import ProjectQgis

class GeometryChanged(QtCore.QObject):

    def __init__(self, iface, dataLogin=False):
        super(GeometryChanged, self).__init__()
        self.iface = iface

    def validate(self):
        geom_change = self.iface.activeLayer().editBuffer().changedGeometries()
        if geom_change:
            self.test_geom_in_moldura(geom_change)

    def test_geom_in_moldura(self, geom_change):
        variable_name = u'area_trabalho_poligono'
        ewkt = ProjectQgis(self.iface).getVariableLayer(variable_name)
        if ewkt:
            wkt = ewkt.split(';')[1]
            geom = core.QgsGeometry.fromWkt(wkt)
            for id_feat in geom_change:
                feat_geom = geom_change[id_feat]
                if geom.intersects(feat_geom) == False:
                    active_lyr = self.iface.activeLayer()
                    QtGui.QMessageBox.critical(
                        self.iface.mainWindow() ,  
                        u'ERRO!' ,  
                        u'''
                        <p style="color:red">
                            Aquisicão da camada {0} está fora do limite de trabalho!
                        </p>
                        '''.format(active_lyr.name())
                    )
                    active_lyr.undoStack().undo()             
        self.iface.mapCanvas().refresh()
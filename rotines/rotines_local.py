#! -*- coding: utf-8 -*-
from qgis import core, gui
from PyQt4 import QtCore, QtGui
import re, sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))

# -*- coding: utf-8 -*-
class Rotines_Local(QtCore.QObject):

    finish = QtCore.pyqtSignal(str)

    def __init__(self, iface, data, tool_interface):
        super(Rotines_Local, self).__init__()
        self.iface = iface
        self.data = data
        self.postgres = tool_interface.loadPostgresDatabase()
        self.tool_interface = tool_interface

    def run(self):
        count_flags = 0
        self.tool_interface.rotinesProgressBar.setMaximum(100)
        self.tool_interface.rotinesProgressBar.setValue(50)
        if u"notSimpleGeometry" in self.data:    
            for param in self.data[u"notSimpleGeometry"]:
                layer = param['camada']
                flag_layer = param['camada_apontamento']
                v_layer = self.getLayerByName(param['camada'])
                if not(v_layer):
                    return
                f_ids = ",".join([str(int(item)) for item in v_layer.allFeatureIds()])
                count_flags += self.run_not_simple_geometry(flag_layer, layer, f_ids)
        elif u"outOfBoundsAngles" in self.data:
            for param in self.data[u"outOfBoundsAngles"]:
                layer = param['camada']
                flag_layer = param['camada_apontamento']
                v_layer = self.getLayerByName(param['camada'])
                if not(v_layer):
                    return
                geom_type = v_layer.geometryType()
                f_ids = ",".join([str(int(item)) for item in v_layer.allFeatureIds()])
                angle = param[u'angle']
                count_flags += self.run_out_of_bounds_angles(layer, f_ids, angle, flag_layer, geom_type)
        elif u"invalidGeometry" in self.data:
            for param in self.data[u"invalidGeometry"]:
                layer = param['camada']
                flag_layer = param['camada_apontamento']
                v_layer = self.getLayerByName(param['camada'])
                if not(v_layer):
                    return
                f_ids = ",".join([str(int(item)) for item in v_layer.allFeatureIds()])
                count_flags += self.run_invalid_geometry(flag_layer, layer, f_ids)
        self.tool_interface.rotinesProgressBar.setValue(0)
        self.finish.emit(u"Rotina executada! Foram gerados '{0}' flags.".format(count_flags))


    def getLayerByName(self, lyrName):
        dbname = self.postgres.getConnectionData()['dbname']
        result = core.QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in result:
            uriClass = core.QgsDataSourceURI(layer.styleURI())
            test = (
                (dbname == layer.source().split(' ')[0][8:-1]) and
                (lyrName == uriClass.table())
            )
            if test:
                self.iface.setActiveLayer(layer)
                if self.iface.activeLayer().allFeatureIds():
                    return self.iface.activeLayer()
        QtGui.QMessageBox.critical(
            self.iface.mainWindow(),
            u"Erro", 
            u"Camada está vazia ou não foi carregada."
        )
        return False

    def run_invalid_geometry(self, flag_layer, layer, f_ids):
        SQL = u'''
            INSERT INTO edgv."{0}"(geom, observacao) 
            SELECT 
                st_asewkt(ST_Multi(ST_SetSrid(ST_Buffer(location(ST_IsValidDetail(f.geom, 0)), 1), ST_Srid(f.geom)))) AS geom,
                '{1}' as observacao 
            FROM (
                SELECT 
                    id, 
                    geom 
                FROM ONLY edgv."{2}" 
                WHERE ST_IsValid(geom) = 'f' AND id IN ({3})
            ) AS f returning *;'''.format(flag_layer, u'Geometria inválida', layer, f_ids)
        pg_cursor = self.postgres.connectionPsycopg2.cursor()
        pg_cursor.execute(SQL)
        return len(pg_cursor.fetchall())
    
    def run_not_simple_geometry(self, flag_layer, layer, f_ids):
        SQL = u'''
            INSERT INTO edgv."{0}"(geom, observacao) 
            SELECT 
                st_asewkt(ST_MULTI(ST_SetSrid(st_buffer(st_startpoint(foo.geom),1), st_srid(foo.geom)))) AS geom,
                '{1}' AS obs 
            FROM (
                SELECT
                    id,
                    (ST_Dump(ST_Node(ST_MakeValid(geom)))).geom AS geom
                FROM edgv."{2}"  
                WHERE ST_IsSimple(geom) = 'f' AND id IN ({3})) AS foo 
            WHERE st_equals(st_startpoint(foo.geom), st_endpoint(foo.geom)) returning *;'''.format(
                flag_layer, u'Geometria inválida', layer, f_ids
            )
        pg_cursor = self.postgres.connectionPsycopg2.cursor()
        pg_cursor.execute(SQL)
        return len(pg_cursor.fetchall())

    def run_out_of_bounds_angles(self, layer, f_ids, angle, flag_layer, geom_type):
        if geom_type == core.QGis.Line: 
            SQL = u"""
            WITH result AS (
                SELECT 
                    points.id, 
                    points.anchor, 
                    (
                        degrees(
                            ST_Azimuth(points.anchor, points.pt1) 
                            - ST_Azimuth(points.anchor, points.pt2)
                        )::decimal + 360
                    ) % 360 AS angle
                FROM
                (
                    SELECT
                        ST_PointN(geom, generate_series(1, ST_NPoints(geom)-2)) as pt1, 
                        ST_PointN(geom, generate_series(2, ST_NPoints(geom)-1)) as anchor,
                        ST_PointN(geom, generate_series(3, ST_NPoints(geom))) as pt2,
                        linestrings.id as id 
                    FROM
                        (
                            SELECT 
                                id, 
                                (ST_Dump(geom)).geom as geom
                            FROM ONLY edgv."{2}"
                            WHERE id IN ({3}) 
                        ) AS linestrings 
                    WHERE ST_NPoints(linestrings.geom) > 2 
                ) as points
            )
            INSERT INTO edgv."{0}"(geom, observacao) 
            SELECT 
                DISTINCT 
                st_asewkt(ST_MULTI(ST_SetSRID(ST_Buffer(anchor, 1), ST_Srid(anchor)))) as geom, 
                '{1}' as obs 
            FROM result 
            WHERE 
                (result.angle % 360) < {4} 
                OR result.angle > (360.0 - ({4} % 360.0)) 
                returning *;""".format(
                    flag_layer, u'Ângulo fora do limite', layer, f_ids, angle
            )
        elif geom_type == core.QGis.Polygon:
            SQL = u"""
            WITH result AS (
                SELECT 
                    points.id, 
                    points.anchor, 
                    (
                        degrees(
                                ST_Azimuth(points.anchor, points.pt1) 
                                - ST_Azimuth(points.anchor, points.pt2)
                        )::decimal + 360
                    ) % 360 AS angle
                FROM (
                    SELECT
                        ST_PointN(geom, generate_series(1, ST_NPoints(geom)-1)) AS pt1,
                        ST_PointN(geom, generate_series(1, ST_NPoints(geom)-1) %  (ST_NPoints(geom)-1)+1) AS anchor,
                        ST_PointN(geom, generate_series(2, ST_NPoints(geom)) %  (ST_NPoints(geom)-1)+1) AS pt2,
                        linestrings.id AS id
                    FROM (
                        SELECT 
                            id, 
                            (ST_Dump(ST_Boundary(ST_ForceRHR((ST_Dump(geom)).geom)))).geom AS geom
                        FROM only edgv."{2}" 
                        WHERE id IN ({3}) 
                    ) AS linestrings 
                    WHERE ST_NPoints(linestrings.geom) > 2 
                ) AS points
            )
            INSERT INTO edgv."{0}"(geom, observacao) 
            SELECT 
                DISTINCT 
                st_asewkt(ST_MULTI(ST_SetSRID(ST_Buffer(anchor, 1), ST_Srid(anchor)))) as geom, 
                '{1}' as obs
            FROM result 
            WHERE (result.angle % 360) < {4} OR result.angle > (360.0 - ({4} % 360.0)) returning *;""".format( 
                flag_layer, u'Ângulo fora do limite', layer, f_ids, angle
            )
        pg_cursor = self.postgres.connectionPsycopg2.cursor()
        pg_cursor.execute(SQL)
        return len(pg_cursor.fetchall())
       
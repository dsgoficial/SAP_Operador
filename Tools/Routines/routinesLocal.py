#! -*- coding: utf-8 -*-
from qgis import core, gui
from PyQt5 import QtCore
import re, sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from Database.postgresql import Postgresql
from SAP.managerSAP import ManagerSAP
from utils import managerQgis, network, msgBox

class RoutinesLocal(QtCore.QObject):

    def __init__(self, iface):
        super(RoutinesLocal, self).__init__()
        self.iface = iface
        self.sap_mode = False
        self.running = False

    def init_postgresql(self):
        self.postgresql = Postgresql()
        sap_data = ManagerSAP().load_data()
        db_data = sap_data['dados']['atividade']['banco_dados']
        db_name = db_data['nome']
        self.postgresql.set_connections_data({
            'db_name' : db_name,
            'db_host' : db_data['servidor'],
            'db_port' : db_data['porta'],
            'db_user' : sap_data['user'],
            'db_password' : sap_data['password'] 
        })
    
    def get_routines_data(self):
        local_routines = {}
        if self.sap_mode:
            sap_data = ManagerSAP().load_data()['dados']['atividade']
            local_routines = sap_data['rotinas']
            description = {
                u"notSimpleGeometry" : u"Identifica geometrias não simples.",
                u"outOfBoundsAngles" : u"Identifica ângulos fora da tolerância.",
                u"invalidGeometry" : u"Identifica geometrias inválidas."
            }
            for name in local_routines:
                local_routines[name]['description'] = description[name]
                local_routines[name]['type_routine'] = 'local'
        return local_routines

    def run(self, routine_data):
        self.init_postgresql()
        count_flags = 0
        if u"notSimpleGeometry" in routine_data:    
            for param in routine_data[u"notSimpleGeometry"]:
                layer_name = param['camada']
                flag_layer = param['camada_apontamento']
                v_layer = self.get_layer_by_name(layer_name)
                if not(v_layer):
                    return
                f_ids = ",".join([str(int(item)) for item in v_layer.allFeatureIds()])
                count_flags += self.run_not_simple_geometry(
                    flag_layer, 
                    layer, 
                    f_ids
                )
        elif u"outOfBoundsAngles" in routine_data:
            for param in routine_data[u"outOfBoundsAngles"]:
                layer_name = param['camada']
                flag_layer = param['camada_apontamento']
                v_layer = self.get_layer_by_name(layer_name)
                if not(v_layer):
                    return
                geom_type = v_layer.geometryType()
                f_ids = ",".join([str(int(item)) for item in v_layer.allFeatureIds()])
                angle = param[u'angle']
                count_flags += self.run_out_of_bounds_angles(
                    layer, 
                    f_ids, 
                    angle, 
                    flag_layer, 
                    geom_type
                )
        elif u"invalidGeometry" in routine_data:
            for param in routine_data[u"invalidGeometry"]:
                layer_name = param['camada']
                flag_layer = param['camada_apontamento']
                v_layer = self.get_layer_by_name(layer_name)
                if not(v_layer):
                    return
                f_ids = ",".join([str(int(item)) for item in v_layer.allFeatureIds()])
                count_flags += self.run_invalid_geometry(
                    flag_layer, 
                    layer, 
                    f_ids
                )
        html = u'''<p style="color:red">
            Rotina executada! Foram gerados {0} flags.
        </p>'''.format(count_flags)
        msgBox.show(text=html, title=u"Aviso")


    def get_layer_by_name(self, layer_name):
        dbname = self.postgres.getConnectionData()['dbname']
        result = core.QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in result:
            uriClass = core.QgsDataSourceURI(layer.styleURI())
            test = (
                (dbname == layer.source().split(' ')[0][8:-1]) and
                (layer_name == uriClass.table()) and
                layer.allFeatureIds()
            )
            if test:
                self.iface.setActiveLayer(layer)
                return self.iface.activeLayer()
        html = u'''<p style="color:red">
            Camada está vazia ou não foi carregada.
        </p>'''
        msgBox.show(text=html, title=u"Erro", status='critical')
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
        result = self.postgresql.run_sql(SQL)
        return len(result)
    
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
        result = self.postgresql.run_sql(SQL)
        return len(result)

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
        result = self.postgresql.run_sql(SQL)
        return len(result)
       
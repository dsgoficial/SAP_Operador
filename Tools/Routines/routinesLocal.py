#! -*- coding: utf-8 -*-
from qgis import core, gui
from PyQt5 import QtCore
import re, sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from Database.postgresql import Postgresql
from SAP.managerSAP import ManagerSAP
from utils import network, msgBox
from utils.managerQgis import ManagerQgis
import processing, json

class RoutinesLocal(QtCore.QObject):

    message = QtCore.pyqtSignal(str)

    def __init__(self, iface):
        super(RoutinesLocal, self).__init__()
        self.iface = iface
        self.sap_mode = False
        self.is_running = False

    def init_postgresql(self):
        self.postgresql = Postgresql()
        sap_data = ManagerSAP(self.iface).load_data()
        db_connection = sap_data['dados']['atividade']['banco_dados']
        db_name = db_connection['nome']
        self.postgresql.current_db_name = db_name
        self.postgresql.set_connections_data({
            'db_name' : db_name,
            'db_host' : db_connection['servidor'],
            'db_port' : db_connection['porta'],
            'db_user' : sap_data['user'],
            'db_password' : sap_data['password'] 
        })
    
    def get_routines_data(self):
        local_routines_formated = []
        if self.sap_mode:
            sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
            local_routines = sap_data['rotinas']
            description = {
                "notSimpleGeometry" : u"Identifica geometrias não simples.",
                "outOfBoundsAngles" : u"Identifica ângulos fora da tolerância.",
                "invalidGeometry" : u"Identifica geometrias inválidas.",
            }
            for name in local_routines:
                d = {
                    name : local_routines[name], 
                    'description' : description[name],
                    'type_routine' : 'local'
                }
                local_routines_formated.append(d)
        if self.is_active_rules_statistics() and not(self.sap_mode) or (self.sap_mode and sap_data['regras']) :
            d = {
                'ruleStatistics' : [], 
                'description' : u"Estatísticas de regras.",
                'type_routine' : 'local'
            }
            local_routines_formated.append(d)
        return local_routines_formated

    def is_active_rules_statistics(self):
        for alg in core.QgsApplication.processingRegistry().algorithms():
            if "dsgtools:rulestatistics" == alg.id():
                return True
        return False

    def run_rule_statistics(self, routine_data):
        html = ''
        rules_data = self.postgresql.get_rules_data()
        parameters = self.get_paremeters_rule_statistics(rules_data)
        if not parameters['INPUTLAYERS']:
            html += '''<p style="color:red">
                    Não há camadas carregadas.
                </p>'''
        if not parameters['RULEDATA']:
            html += '''<p style="color:red">
                    Não há regras no banco.
                </p>'''
        if not html:
            proc = processing.run(
                "dsgtools:rulestatistics", 
                parameters
            )
            for line in proc['RESULT'].split('\n\n'):
                if '[regras]' in line.lower():
                    html+='<h3>{0}</h3>'.format(line)
                elif 'passaram' in line.lower():
                    html += u"<p style=\"color:green\">{0}</p>".format(line)
                else:
                    html += u"<p style=\"color:red\">{0}</p>".format(line)   
        self.message.emit(html)

    def get_paremeters_rule_statistics(self, rules_data):
        parameters = { 
            'INPUTLAYERS' : [], 
            'RULEFILE' : '.json', 
            'RULEDATA' : json.dumps(rules_data) 
        }
        m_qgis = ManagerQgis(self.iface)
        layers = m_qgis.get_loaded_layers()
        for lyr in layers:
            data_provider = lyr.dataProvider().uri()
            if not data_provider.database():
                continue
            parameters['INPUTLAYERS'].append(
                'dbname=\'{0}\' host={1} port={2} user=\'{3}\' password=\'{4}\' key=\'id\' table=\"{5}\".\"{6}\" (geom) sql={7}'.format(
                    data_provider.database(),
                    data_provider.host(),
                    data_provider.port(),
                    data_provider.username(),
                    data_provider.password(),
                    data_provider.schema(),
                    data_provider.table(),
                    data_provider.sql()
                )
            )
        return parameters

    def run(self, routine_data):
        self.init_postgresql()
        count_flags = 0
        if u"ruleStatistics" in routine_data:
            self.run_rule_statistics(routine_data)
            return
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
                    layer_name, 
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
                    layer_name, 
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
                    layer_name, 
                    f_ids
                )
        html = u'''<p style="color:red">
            Rotina executada! Foram gerados {0} flags.
        </p>'''.format(count_flags)
        self.message.emit(html)


    def get_layer_by_name(self, layer_name):
        db_name = self.postgresql.load_data()['db_name']
        m_qgis = ManagerQgis(self.iface)
        result = m_qgis.get_loaded_layers()
        for layer in result:
            uri_class = core.QgsDataSourceUri(layer.styleURI())
            test = (
                (db_name == layer.source().split(' ')[0][8:-1]) and
                (layer_name == uri_class.table()) and
                layer.allFeatureIds()
            )
            if test:
                self.iface.setActiveLayer(layer)
                return self.iface.activeLayer()
        html = u'''<p style="color:red">
            Camada está vazia ou não foi carregada.
        </p>'''
        self.message.emit(html)
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
       
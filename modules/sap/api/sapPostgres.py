import psycopg2
from psycopg2 import sql
from functools import wraps

def transaction(func):
    @wraps(func)
    def inner(*args, **kwargs):
        args = list(args[:])
        conn = args[0].getConnection()
        cursor = conn.cursor()
        args.insert(1, cursor)
        query = []
        try:
            query = func(*args, **kwargs)
            conn.commit()
        except Exception as e:
            conn.rollback()
            cursor.close()
            raise Exception("{} error: {}".format(func.__name__, e))
        cursor.close()
        return query
    return inner

def notransaction(func):
    @wraps(func)
    def inner(*args, **kwargs):
        args = list(args[:])
        conn = args[0].getConnection()
        cursor = conn.cursor()
        args.insert(1, cursor)
        query = []
        try:
            query = func(*args, **kwargs)
            return query
        except Exception as e:
            cursor.close()
            raise Exception("{} error: {}".format(func.__name__, e))
    return inner

class SapPostgres:
    
    def __init__(self):
        super(SapPostgres, self).__init__()
        self.connection = None
        self.connectionSettings = {}
        
    def setConnection(self, dbUser, dbPassword, dbHost, dbPort, dbName):
        self.connection = psycopg2.connect(
            u"dbname='{0}' user='{1}' host='{2}' port='{3}' password='{4}'".format(
                dbName, dbUser, dbHost, dbPort, dbPassword
            )
        )
        self.setConnectionSettings(dbUser, dbPassword, dbHost, dbPort, dbName)

    def getConnection(self):
        return self.connection

    def setConnectionSettings(self, dbUser, dbPassword, dbHost, dbPort, dbName):
        self.connectionSettings = {
            'user': dbUser,
            'password': dbPassword,
            'host': dbHost,
            'port': dbPort,
            'name': dbName
        }

    def getConnectionSettings(self):
        return self.connectionSettings

    def getActivity(self):
        return {
            'layers': self.getLayers(),
            'database': self.getConnectionSettings(),
            'rules': self.getRules(),
            'styles': self.getStyles(),
            'workspaces': self.getWorkspaces(),
            'qgisModels': self.getQgisModels(),
            'menus': self.getMenus(),
            'qgisShortcut': self.getQgisShortcut()
        }

    @notransaction
    def getLayers(self, cursor):
        cursor.execute(
            sql.SQL('''
                SELECT 
                    f_table_schema, 
                    f_table_name, 
                    type 
                FROM 
                    geometry_columns
                WHERE 
                    f_table_schema = 'edgv'; 
            '''
            )
        )
        query = cursor.fetchall()
        return [{
            'schema': item[0],
            'nome': item[1],
            'geometryType': item[2] 
        } for item in query]

    @notransaction
    def getRules(self, cursor):
        cursor.execute(
            sql.SQL('''
                SELECT 
                    b.id AS "ordem",
                    camada,
                    atributo,
                    regra,
                    cor_rgb,
                    grupo_regra,
                    descricao 
                FROM 
                    layer_rules AS a 
                INNER JOIN 
                    group_rules AS b 
                ON a.grupo_regra_id = b.id ; 
            '''
            )
        )
        query = cursor.fetchall()
        return [{
            'ordem': item[0],
            'camada': item[1],
            'atributo': item[2],
            'regra': item[3],
            'cor_rgb': item[4],
            'grupo_regra': item[5],
            'descricao': item[6],
            'tipo_regra': 'atributo'
        } for item in query]


    @notransaction
    def getStyles(self, cursor):
        cursor.execute(
            sql.SQL('''
                SELECT 
                    f_table_schema,
                    f_table_name,
                    stylename,
                    styleqml
                FROM 
                    layer_styles; 
            '''
            )
        )
        query = cursor.fetchall()
        return [{
            'f_table_schema': item[0],
            'f_table_name': item[1],
            'stylename': item[2],
            'styleqml': item[3]
        } for item in query]


    @notransaction
    def getWorkspaces(self, cursor):
        cursor.execute(
            sql.SQL('''
                SELECT 
                    nome,
                    ST_asEWkt(geom)
                FROM 
                    work_areas; 
            '''
            )
        )
        query = cursor.fetchall()
        return [{
            'nome': item[0],
            'ewkt': item[1]
        } for item in query]

    @notransaction
    def getMenus(self, cursor):
        cursor.execute(
            sql.SQL('''
                SELECT 
                    nome,
                    definicao_menu
                FROM 
                    qgis_menus; 
            '''
            )
        )
        query = cursor.fetchall()
        return [{
            'nome': item[0],
            'menu_json': item[1]
        } for item in query]

    @notransaction
    def getQgisModels(self, cursor):
        cursor.execute(
            sql.SQL('''
                SELECT 
                    nome,
                    descricao,
                    model_xml
                FROM 
                    qgis_models; 
            '''
            )
        )
        query = cursor.fetchall()
        return [{
            'nome': item[0],
            'descricao': item[1],
            'model_xml': item[2]
        } for item in query]

    @notransaction
    def getQgisShortcut(self, cursor):
        cursor.execute(
            sql.SQL('''
                SELECT 
                    descricao,
                    ferramenta,
                    atalho
                FROM 
                    qgis_shortcuts; 
            '''
            )
        )
        query = cursor.fetchall()
        return [{
            'descricao': item[0],
            'ferramenta': item[1],
            'atalho': item[2]
        } for item in query]
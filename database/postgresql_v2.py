#! -*- coding: utf-8 -*-
import psycopg2
import json
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSettings
from qgis.core import QgsMapLayerRegistry, QgsVectorLayer, QgsDataSourceURI, QgsPoint, QGis, QgsGeometry, QgsProject, QgsField, QgsRelation, QgsCoordinateReferenceSystem
import json, sys, os, copy, base64
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from managerQgis.projectQgis import ProjectQgis

class Postgresql_v2(object):
    def __init__(self, iface=False):
        # contrutor
        super(Postgresql_v2, self).__init__()
        self.iface = iface
        self.connectionLoginData = None 
        self.connectionPsycopg2 = None
        self.dbJson = None
        self.dbAlias = None
        self.modeRemote = None
        self.geom = None

    def getAliasNamesDb(self):
        # retorna uma lista com os apelidos de cada banco postgres validado
        settings  = QSettings().allKeys()
        infoDataBases = [s for s in settings if 'PostgreSQL' == s.split("/")[0]
            and 'connections' == s.split("/")[1]
        ]
        aliasesDb = list(set([a.split("/")[-2] for a in infoDataBases \
                            if a.split("/")[-2] != u'connections']))
        return aliasesDb

    def encrypt(self, key, plaintext):
        return base64.b64encode(plaintext)

    def decrypt(self, key, ciphertext):
        return base64.b64decode(ciphertext)


    def getConnectionData(self):
        dbAlias = self.dbAlias
        settings  = QtCore.QSettings()
        if settings.value(u'PostgreSQL/connections/%s/database'%(dbAlias)):
            connection = {
                'aliasDb' : dbAlias,
                'dbname':settings.value(u'PostgreSQL/connections/%s/database'%(dbAlias)),
                'user':settings.value(u'PostgreSQL/connections/%s/username'%(dbAlias)),
                'host':settings.value(u'PostgreSQL/connections/%s/host'%(dbAlias)),
                'password':settings.value(u'PostgreSQL/connections/%s/password'%(dbAlias)),
                'port':settings.value(u'PostgreSQL/connections/%s/port'%(dbAlias)),
            }
        elif self.connectionLoginData:
            connection = self.connectionLoginData
        else:
            connection = json.loads(self.decrypt('123456', ProjectQgis(self.iface).getVariableProject('loginData', isJson=True)))
        return connection

    def connectPsycopg2WithLoginData(self, loginData):
        self.dbAlias = loginData["dados"]["atividade"]["banco_dados"]["nome"]
        self.modeRemote = True
        self.geom = loginData["dados"]["atividade"]["geom"]
        self.connectionLoginData = {
            "user" : loginData["user"],
            "password" : loginData["password"],
            "host" : loginData["dados"]["atividade"]["banco_dados"]["servidor"],
            "port" : loginData["dados"]["atividade"]["banco_dados"]["porta"],
            "dbname" : self.dbAlias
        }
        conn = psycopg2.connect(
            """dbname='%s' user='%s' host='%s' port='%s' password='%s'"""%( 
                self.connectionLoginData['dbname'], 
                self.connectionLoginData['user'], 
                self.connectionLoginData['host'],
                self.connectionLoginData['port'], 
                self.connectionLoginData['password']
            )
        )
        ProjectQgis(self.iface).setProjectVariable(
            'loginData', 
            self.encrypt('123456', json.dumps(copy.deepcopy(self.connectionLoginData)))
        )
        conn.set_session(autocommit=True)
        self.connectionPsycopg2 = conn
        self.createDataBaseJSON(loginData)

    def connectPsycopg2(self, dbAlias):
        # conexão via psycopg2
        self.dbAlias = dbAlias
        c = self.getConnectionData()
        conn = psycopg2.connect(
            """dbname='%s' user='%s' host='%s' port='%s' password='%s'"""\
            %(c['dbname'], c['user'], c['host'], c['port'], c['password'])
        )
        conn.set_session(autocommit=True)
        self.connectionPsycopg2 = conn
        self.createDataBaseJSON()
        
    def getWorkspaceItems(self):
        lyr_data = self.getTableFromDb('aux_moldura_a')
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute('''
            SELECT
            mi
            FROM {}.{};'''.format(lyr_data['schema'], lyr_data['layer'])
        )
        query = postgresCursor.fetchall()
        workspace = list(set([item[0] for item in query]))
        return workspace

    def getStylesItems(self, styles_name=False):
        if self.getTableFromDb('layer_styles'):
            if styles_name:
                styles = ", ".join([ "'%{}%'".format(name) for name in styles_name])
                sql = '''SELECT stylename FROM layer_styles where stylename like any(array[{}]);'''.format(styles)
            else:
                sql = '''SELECT stylename FROM layer_styles;'''
            postgresCursor = self.connectionPsycopg2.cursor()
            postgresCursor.execute(sql)
            query = postgresCursor.fetchall()
            if query[0]:
                sep = '/' if '/' in query[0][0] else '_'
                styles = list(set([item[0].split(sep)[0] for item in query]))
                return styles
        return []

    def getRulesData(self):
        if self.getTableFromDb('layer_rules'):
            postgresCursor = self.connectionPsycopg2.cursor()
            postgresCursor.execute('''
                SELECT
                id,
                tipo_regra, 
                camada, 
                nome, 
                cor_rgb, 
                regra, 
                tipo_estilo, 
                atributo, 
                descricao,
                ordem 
                FROM public.layer_rules ;
            ''')
            query = postgresCursor.fetchall()
            rules =  {row[0] : {
                'tipo_regra' : row[1],
                'camada' : row[2],
                'nome' : row[3],
                'corRgb' : [ 
                    int(row[4].split(',')[0]), 
                    int(row[4].split(',')[1]), 
                    int(row[4].split(',')[2])
                ],
                'cor_rgb' : row[4],
                'regra' : row[5],
                'tipo_estilo' : row[6],
                'atributo' : row[7],
                'descricao' : row[8],
                'ordem' : row[9]
            } for row in query}
            return rules
        return {}

    def getProfilesData(self):
        #retorna um dicionário com todos os perfis do menu de aquisição
        if self.getTableFromDb('menu_profile'):
            postgresCursor = self.connectionPsycopg2.cursor()
            postgresCursor.execute('''
                SELECT
                id,
                nome_do_perfil,
                descricao,
                perfil,
                ordem_menu
                FROM public.menu_profile ;
            ''')
            query = postgresCursor.fetchall()
            profiles =  {row[0] : {
                'nome_do_perfil' : row[1],
                'descricao' : row[2],
                'perfil' : row[3],
                'orderMenu' : row[4]
            } for row in query}
            return profiles
        return {}
              
    def getTable(self, tableName):
        layer_data = self.getTableFromDb(tableName)
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(
            '''SELECT * FROM {}.{};'''.format(layer_data['schema'], layer_data['layer'])
        )
        query = postgresCursor.fetchall()
        return query

    def saveProfile(self, data):
        if not self.getTableFromDb('menu_profile'):
            self.createProfileTable()
        if self.checkIfExistsProfile(data['profileName']):
            self.updateProfileOnDb(data)
        else:
            self.insertProfileOnDb(data)

    def getFilterOption(self):
        filterData = self.getFilterData()
        filterOption = []
        for x in filterData:
            filterOption.append(filterData[x]['tipo_filtro'])
        return filterOption

    def getFilterData(self):
        if self.getTableFromDb(u'layer_filter'):
            postgresCursor = self.connectionPsycopg2.cursor()
            postgresCursor.execute('''
                SELECT
                id,
                camada,
                tipo_filtro,
                filtro
                FROM public.layer_filter ;
            ''')
            query = postgresCursor.fetchall()
            filterData =  {row[0] : {
                'camada' : row[1],
                'tipo_filtro' : row[2],
                'filtro' : row[3]
            } for row in query}
            return filterData
        return {}
            
    def getTableFromDb(self, tableName):
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(
            '''
            SELECT table_schema, table_name FROM information_schema.tables where table_name = '{}';
            '''.format(tableName))
        query = postgresCursor.fetchall()
        if query:
            return { 'schema' : query[0][0], 'layer' : query[0][1] }
        return {}

    def checkIfExistsProfile(self, profileName):
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(
            '''
            SELECT
            id
            FROM menu_profile
            WHERE nome_do_perfil = '{0}';
            '''.format(profileName)
        )
        query = postgresCursor.fetchall()
        result = list(set([item[0] for item in query]))
        return result

    def createProfileTable(self):
        #Método para criar a tabela de perfis de menu
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(
            '''
            CREATE TABLE menu_profile
            (
                id SERIAL PRIMARY KEY,
                nome_do_perfil text NOT NULL,
                descricao text ,
                perfil json NOT NULL,
                ordem_menu json NOT NULL
            ); grant all on public.menu_profile to public;
            '''
        )

    def updateProfileOnDb(self, data):
        profileName = data['profileName']
        profile = data['profile']
        orderMenu = data['orderMenu']
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(
            '''
            UPDATE
            menu_profile
            SET perfil = '{0}', ordem_menu = '{1}' 
            WHERE nome_do_perfil = '{2}'
            '''.format(
                json.dumps(profile),
                json.dumps(orderMenu), 
                profileName
            )
        )
    
    def insertProfileOnDb(self, data):
        #Método para inserir um perfil na
        #tabela de perfis de menu
        profileName = data['profileName']
        profileJson = data['profile']
        orderMenu = data['orderMenu']
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(
            '''
            INSERT INTO public.menu_profile
            (
                nome_do_perfil,
                perfil,
                ordem_menu
            )
            VALUES
            (
                '{0}',
                '{1}',
                '{2}'
            )
            '''.format(
                profileName, 
                json.dumps(profileJson),
                json.dumps(orderMenu)
            )
        )
    
    def createDataBaseJSON(self, loginData=False):
        if loginData:
            layers_name = [data['nome'] for data in loginData['dados']['atividade']['camadas']]
            layers_data = self.getAllLayersByName(layers_name)
        else:
            layers_data = self.getAllLayersByName()
            layers_name = [ data['layer'] for data in layers_data]
        jsonDb = self.getTemplateJsonDb()
        dbname = jsonDb['dataConnection']['dbname']
        tablesWithFilterColumn = self.getAllTablesByColumnName('filter')
        jsonDb['listOfLayers'] = layers_name
        for lyr_data in layers_data:
            layer_name = lyr_data['layer']
            constraint = self.getContrainsCodes(layer_name)
            geom = self.getGroupGeomOfLayer(layer_name)
            group = self.getGroupClassOfLayer(layer_name)
            check_layer = ( (True if geom else False) and (True if group else False) )
            if check_layer:
                if not(group in jsonDb[dbname][geom]):
                    jsonDb[dbname][geom][group] = {}
                jsonDb[dbname][geom][group][layer_name] = {}
                jsonDb[dbname][geom][group][layer_name]['schema'] = lyr_data['schema']
                fields = self.getFieldsOfLayer(lyr_data)
                domains = self.getDomainsOfLayer(lyr_data)
                for field in list(set(domains.keys() + fields)):
                    jsonDb[dbname][geom][group][layer_name][field] = {}
                    if tablesWithFilterColumn and (field in domains) and  (domains[field] in tablesWithFilterColumn):
                        table = self.getTable(domains[field])
                        jsonDb[dbname][geom][group][layer_name]['filter'] = table
                    data = {
                        'domains' : domains,
                        'dbname' : dbname,
                        'geom'  : geom,
                        'group' : group,
                        'layer' : layer_name,
                        'field' : field,
                        'jsonDb' : jsonDb,
                        'constraint' : constraint 
                    }
                    self.loadValueMapOfField(data)
        self.dbJson = jsonDb
    
    def getTemplateJsonDb(self):
        dataBase = {
            self.getConnectionData()['dbname'] : {
                'PONTO' : {},
                'LINHA' : {},
                'AREA'  : {},
            },
            'dataConnection' : self.getConnectionData(),
            'listOfLayers' : [],
            'styles' : self.loadStyles(),
            'workspaces' : self.loadWorkspaces() if not(self.modeRemote) else self.geom,
            'srid' : self.getSrid(),
        }
        return dataBase

    def loadStyles(self):
        if self.getTableFromDb('layer_styles'):
            postgresCursor = self.connectionPsycopg2.cursor()
            postgresCursor.execute('''  SELECT
                                        stylename, id
                                        FROM
                                        layer_styles;
                                        ''')
            query = postgresCursor.fetchall()
            items = {item : value for item, value in query}
            return items
        return {}

    def loadWorkspaces(self):
        lyr_data = self.getTableFromDb('aux_moldura_a')
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(u'''  SELECT
                                    mi, st_asewkt(geom)
                                    FROM
                                    {}.{};
                                      '''.format(lyr_data['schema'], lyr_data['layer']))
        query = postgresCursor.fetchall()
        items = {item : value for item, value in query}
        return items

    def getAllLayersByName(self, layers_name=False):
        postgresCursor = self.connectionPsycopg2.cursor()
        if layers_name:
            list_names = ", ".join([ "'%{}%'".format(name) for name in layers_name])
            sql = '''select f_table_schema, f_table_name from geometry_columns
                where f_table_name like any(array[{}]);'''.format(list_names)
        else:
            sql = "select f_table_schema, f_table_name from geometry_columns;"
        postgresCursor.execute(sql)
        query = postgresCursor.fetchall()
        layers = [ {'schema' : item[0] , 'layer' : item[1]} for item in query ]
        return layers

    def getGroupGeomOfLayer(self, layerName):
        try:
            test = {'a' : 'AREA', 
                    'c' : 'PONTO',
                    'p' : 'PONTO', 
                    'd' : 'LINHA',
                    'l' : 'LINHA',}
            return test[layerName.split("_")[-1]]
        except:
            return

    def getGroupClassOfLayer(self, layerName):
        # retorna a categoria da camada
        try:
            return layerName.split('_')[0]
        except:
            return

    def loadValueMapOfField(self, data):
        domains = data['domains']  
        dbname = data['dbname'] 
        geom = data['geom'] 
        group = data['group']
        layer = data['layer']
        field = data['field']
        jsonDb = data['jsonDb']
        constraint = data['constraint']
        if field in domains:
            if field in constraint:
                values =  self.getValueMapOfDomain(domains[field], constraint[field])
            else:
                values =  self.getValueMapOfDomain(domains[field])
            values.update({u'IGNORAR' : 10000})
            jsonDb[dbname][geom][group][layer][field]['ValueMap'] = values 
    
    def getValueMapOfDomain(self, domainName, code_list=False):
        layer_data = self.getTableFromDb(domainName)
        if code_list:
            select = '''SELECT code, code_name FROM {}.{} WHERE code IN ({});'''.format(layer_data['schema'], domainName, code_list)
        else:
            select = '''SELECT code, code_name FROM {}.{};'''.format(layer_data['schema'], domainName)
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute( select )
        query = postgresCursor.fetchall()
        data = dict(query)
        inv_data = {v: k for k, v in data.iteritems()}
        return inv_data
    
    def getContrainsCodes(self, layerName):
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute('''
            SELECT d.column_name, c.consrc 
            FROM 
            (SELECT conname, consrc FROM pg_constraint) c
            INNER JOIN 
            (
                SELECT column_name, constraint_name 
                FROM information_schema.constraint_column_usage WHERE table_name =  '{0}'
            ) d 
            ON 
            (c.conname = d.constraint_name and not(d.column_name = 'id'));'''.format(layerName))
        query = postgresCursor.fetchall()
        codes = {}
        for item in query:
            field = item[0]
            text = item[1]
            code_list = []
            for code in " ".join(" ".join(text.split("(")).split(")")).split(" "):
                try:
                    int(code)
                    code_list.append(code)
                except:
                    pass
            codes[field] = ",".join(code_list)
        return codes
      
    def getDomainsOfLayer(self, data_layer):
        # retorna os nomes dos dominios da camada
        layer_name = data_layer['layer']
        layer_schema = data_layer['schema']
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute('''
            SELECT pg_get_constraintdef(c.oid) AS cdef
            FROM pg_constraint c
            JOIN pg_namespace n
            ON n.oid = c.connamespace
            WHERE contype IN ('f')
            AND n.nspname = '{0}'
            AND conrelid::regclass::text IN ('{0}.{1}');'''.format(layer_schema, layer_name))
        query = postgresCursor.fetchall()
        domains = { 
            item[0].split('(')[1].split(')')[0].replace(' ','') : \
            item[0].split('(')[1].split('.')[1] \
            for item in query
            }
        return domains

    def getFieldsOfLayer(self, data_layer):
        layer_name = data_layer['layer']
        layer_schema = data_layer['schema']
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute("""SELECT column_name
                                FROM information_schema.columns
                                WHERE table_schema = '{}'
                                AND table_name   = '{}'
                                AND column_name !~ 'geom' AND column_name !~ 'id'
                               """.format(layer_schema, layer_name))
        query = postgresCursor.fetchall()
        listOfFields = [item[0] for item in query]
        return listOfFields

    def getSrid(self):
        # retorna uma lista com todos os campos da camada
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(u""" 
            select srid from geometry_columns where f_table_name like '%moldura%';
        """)
        query = postgresCursor.fetchall()
        srid = {'srid' : item[0] for item in query}
        return srid
    
    def getAllTablesByColumnName(self, fieldName):
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute("""
            select c.relname
            from pg_class as c
            inner join pg_attribute as a on a.attrelid = c.oid
            where a.attname = '{0}' and c.relkind = 'r'
        """.format(fieldName))
        query = postgresCursor.fetchall()
        tables = [ item[0] for item in query] 
        return tables

       
#! -*- coding: utf-8 -*-
import psycopg2
import json
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSettings
from qgis.core import QgsMapLayerRegistry, QgsVectorLayer, QgsDataSourceURI, QgsPoint, QGis, QgsGeometry, QgsProject, QgsField, QgsRelation, QgsCoordinateReferenceSystem
import json, sys, os, copy, base64
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from managerQgis.projectQgis import ProjectQgis

class Postgresql(object):
    def __init__(self, iface):
        # contrutor
        super(Postgresql, self).__init__()
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
        #cipher = XOR.new(key)
        return base64.b64encode(plaintext)

    def decrypt(self, key, ciphertext):
        #cipher = XOR.new(key)
        return base64.b64decode(ciphertext)


    def getConnectionData(self):
        #retorna um dicionário com os dados de conexão do banco
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
        # conexão via psycopg2
        self.dbAlias = loginData['dbname']
        conn = psycopg2.connect(
            """dbname='%s' user='%s' host='%s' port='%s' password='%s'"""%( 
                loginData['dbname'], 
                loginData['user'], 
                loginData['host'],
                loginData['port'], 
                loginData['password']
            )
        )
        self.connectionLoginData = {
                'aliasDb' : loginData['dbname'],
                'dbname': loginData['dbname'],
                'user': loginData['user'],
                'host': loginData['host'],
                'password': loginData['password'],
                'port': loginData['port']
        }
        ProjectQgis(self.iface).setProjectVariable(
            'loginData', 
            self.encrypt('123456', json.dumps(copy.deepcopy(self.connectionLoginData)))
        )
        conn.set_session(autocommit=True)
        self.connectionPsycopg2 = conn
        self.loadCacheDataBase()

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
        self.loadCacheDataBase()

    def loadCacheDataBase(self):
        # carrega os dados do banco no JSON e adicona em uma variável global
        self.createDataBaseJSON()
        
    def getWorkspaceItems(self):
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute('''
            SELECT
            mi
            FROM edgv.aux_moldura_a;
        ''')
        query = postgresCursor.fetchall()
        workspace = list(set([item[0] for item in query]))
        return workspace

    def getStylesItems(self):
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute('''
            SELECT
            stylename
            FROM layer_styles;
        ''')
        query = postgresCursor.fetchall()
        styles = list(set([item[0].split('_')[0] for item in query]))
        return styles

    def getRulesData(self):
        # retorna um dicionário com todas as regras
        if self.checkIfExistsTable('layer_rules'):
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
        if self.checkIfExistsTable('menu_profile'):
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
        # retorna um dicionário com todos os dados de uma determinada tabela
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(
            '''
            SELECT
            *
            FROM dominios.%s;
            '''%(tableName))
        query = postgresCursor.fetchall()
        return query

    def saveProfile(self, data):
        #Método chamado para salvar perfil
        #no banco de dados
        if not self.checkIfExistsTable('menu_profile'):
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
        if self.checkIfExistsTable(u'layer_filter'):
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
            
    def checkIfExistsTable(self, tableName):
        #Método para verificar se uma determinada
        #tabela existe no banco de dados
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(
            '''
            SELECT
            relname
            FROM pg_class
            WHERE relname = '{0}';
            '''.format(tableName))
        query = postgresCursor.fetchall()
        result = list(set([item[0] for item in query]))
        return result

    def checkIfExistsProfile(self, profileName):
        #Método para verificar se um determinado
        #perfil de menu existe no banco de dados
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
        #Método para atualizar um perfil de menu
        #existente
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
    
    def createDataBaseJSON(self):
        # cria um JSON com os dados necessarios para o plugin
        dbname = self.getConnectionData()['aliasDb']
        jsonDb = self.getJsonDb()
        tablesWithFilterColumn = self.getAllTablesByColumnName('filter')
        for layer in self.getAllLayersNames():
            constraint = self.getContrainsCodes(layer)
            jsonDb['listOfLayers'].append(layer)
            geom = self.getGroupGeomOfLayer(layer)
            group = self.getGroupClassOfLayer(layer)
            checkGeom = True if geom else False
            checkGroup = True if group else False
            if checkGeom and checkGroup:
                if not(group in jsonDb[dbname][geom]):
                    jsonDb[dbname][geom][group] = {}
                jsonDb[dbname][geom][group][layer] = {}
                fields = self.getFieldsOfLayer(layer)
                domains = self.getDomainsOfLayer(layer)
                for field in list(set(domains.keys() + fields)):
                    jsonDb[dbname][geom][group][layer][field] = {}
                    if field in domains and  domains[field] in tablesWithFilterColumn:
                        table = self.getTable(domains[field])
                        jsonDb[dbname][geom][group][layer]['filter'] = table
                    data = {
                        'domains' : domains,
                        'dbname' : dbname,
                        'geom'  : geom,
                        'group' : group,
                        'layer' : layer,
                        'field' : field,
                        'jsonDb' : jsonDb,
                        'constraint' : constraint 
                    }
                    self.loadValueMapOfField(data)
        self.dbJson = jsonDb
    
    def getJsonDb(self):
        # criar o formato inicial do JSON para ser usado
        dataBase = {
            self.getConnectionData()['aliasDb'] : {
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
        # retorna todos os estilos da tabela layer_styles com seus ids
        try:
            postgresCursor = self.connectionPsycopg2.cursor()
            postgresCursor.execute('''  SELECT
                                        stylename, id
                                        FROM
                                        layer_styles;
                                        ''')
            query = postgresCursor.fetchall()
            items = {item : value for item, value in query}
            return items
        except:
            return

    def loadWorkspaces(self):
        # retorna todas as áreas de trabalho 
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute('''  SELECT
                                    mi, st_asewkt(geom)
                                    FROM
                                    edgv.aux_moldura_a;
                                      ''')
        query = postgresCursor.fetchall()
        items = {item : value for item, value in query}
        return items

    def getAllLayersNames(self):
        # retorna todos os nomes das camadas do schema edgv
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute('''  select 
                                    f_table_name 
                                    from geometry_columns 
                                    where f_table_schema ~ 'edgv'
                                      ''')
        query = postgresCursor.fetchall()
        layers = [item[0] for item in query]
        return layers

    def getGroupGeomOfLayer(self, layerName):
        # retorna o grupo de Geometria da camada pelo nome 
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
        # adiciona o mapa de valores do campo
        #tablesFilter = data['tablesFilter']  
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
        # retorna o mapa de valores do dominio
        if code_list:
            select = '''SELECT code, code_name FROM dominios.{0} WHERE code IN ({1});'''.format(domainName, code_list)
        else:
            select = '''SELECT code, code_name FROM dominios.{0};'''.format(domainName)
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute( select )
        query = postgresCursor.fetchall()
        data = dict(query)
        inv_data = {v: k for k, v in data.iteritems()}
        return inv_data
    
    def getContrainsCodes(self, layerName):
        #NOVO
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
      
    def getDomainsOfLayer(self, layerName):
        # retorna os nomes dos dominios da camada
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute('''
            SELECT pg_get_constraintdef(c.oid) AS cdef
            FROM pg_constraint c
            JOIN pg_namespace n
            ON n.oid = c.connamespace
            WHERE contype IN ('f')
            AND n.nspname = 'edgv'
            AND conrelid::regclass::text IN ('edgv.%s');''' % (layerName))
        query = postgresCursor.fetchall()
        domains = { 
            item[0].split('(')[1].split(')')[0].replace(' ','') : \
            item[0].split('(')[1].split('.')[1] \
            for item in query
            }
        return domains

    def getFieldsOfLayer(self, layerName):
        # retorna uma lista com todos os campos da camada
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute("""SELECT column_name
                                FROM information_schema.columns
                                WHERE table_schema = 'edgv'
                                AND table_name   = '%s'
                                AND column_name !~ 'geom' AND column_name !~ 'id'
                               """%(layerName))
        query = postgresCursor.fetchall()
        listOfFields = [item[0] for item in query]
        return listOfFields

    def getSrid(self):
        # retorna uma lista com todos os campos da camada
        postgresCursor = self.connectionPsycopg2.cursor()
        postgresCursor.execute(u""" 
                                SELECT 
                                srid 
                                FROM 
                                geometry_columns where f_table_name ~ 'aux_moldura_a'
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

       
import psycopg2

class Postgres:
    
    def __init__(
            self,
            dbName, 
            dbHost, 
            dbPort, 
            dbUser, 
            dbPassword
        ):
        super(Postgres, self).__init__()
        self.connection = None
        self.setConnection(dbName, dbHost, dbPort, dbUser, dbPassword)
        
    def setConnection(self, dbName, dbHost, dbPort, dbUser, dbPassword):
        self.connection = psycopg2.connect(
            u"dbname='{0}' user='{1}' host='{2}' port='{3}' password='{4}'".format(
                dbName, dbUser, dbHost, dbPort, dbPassword
            )
        )
        self.connection.set_session(autocommit=True)

    def getConnection(self):
        return self.connection

    def getFilterValues(self, layerName, layerSchema):
        tablesWithFilter = self.getTablesbyColumn('filter')
        if not tablesWithFilter:
            return []
        fields = self.getLayerColumns(layerName, layerSchema)
        domains = self.getLayerDomains(layerName, layerSchema)
        for field in fields:
            if not(
                    (field in domains) 
                    and 
                    (domains[field] in tablesWithFilter)
                ):
                continue
            return self.getTableValues('dominio', field)
        
    def getTableValues(self, tableSchema, tableName):
        pgCursor = self.getConnection().cursor()
        pgCursor.execute(
            """SELECT * FROM {}.{};""".format(tableSchema, tableName)
        )
        query = pgCursor.fetchall()
        pgCursor.close()
        if not query:
            return []
        return query

    def getTablesbyColumn(self, columnName):
        pgCursor = self.getConnection().cursor()
        pgCursor.execute(
            """SELECT c.relname
            FROM pg_class AS c
            INNER JOIN pg_attribute AS a ON a.attrelid = c.oid
            WHERE a.attname = '{0}' AND c.relkind = 'r';""".format(columnName)
        )
        query = pgCursor.fetchall()
        pgCursor.close()
        if not query:
            return []
        return [item[0] for item in query]

    def getLayerContrainsCodes(self, layerName):
        pgCursor = self.getConnection().cursor()
        pgCursor.execute(
            """SELECT d.column_name, pg_get_constraintdef(c.oid)
            FROM
            (SELECT conname, oid FROM  pg_constraint) c
            INNER JOIN
            (
                SELECT column_name, constraint_name
                FROM information_schema.constraint_column_usage WHERE table_name = '{0}'
            ) d
            ON (c.conname = d.constraint_name AND not(d.column_name = 'id'));""".format(
                layerName
            )
        )
        query = pgCursor.fetchall()
        pgCursor.close()
        if not query:
            return {}
        result = {}
        for field, text in query:
            if not(field and text):
                return 
            codeList = []
            for code in " ".join(" ".join(text.split("(")).split(")")).split(" "):
                if not code.isnumeric():
                    continue
                codeList.append(code)
            result[field] = ",".join(codeList)
        return result

    def getLayerColumns(self, layerName, layerSchema):
        pgCursor = self.getConnection().cursor()
        pgCursor.execute(
            """SELECT column_name 
            FROM information_schema.columns
            WHERE table_schema = '{0}'
            AND table_name = '{1}'
            AND NOT column_name='geom' AND NOT column_name='id';""".format(
                layerSchema,
                layerName
            )
        )
        query = pgCursor.fetchall()
        pgCursor.close()
        if not query:
            return []
        return [item[0] for item in query]

    def getLayerDomains(self, layerName, layerSchema):
        pgCursor = self.getConnection().cursor()
        pgCursor.execute(
            """SELECT pg_get_constraintdef(c.oid) AS cdef
            FROM pg_constraint c
            JOIN pg_namespace n
            ON n.oid = c.connamespace
            WHERE contype IN ('f')
            AND n.nspname = '{0}'
            AND (
                conrelid::regclass::text IN ('{0}.{1}')
                or
                conrelid::regclass::text IN ('{1}')
            );
            """.format(
                layerSchema,
                layerName
            )
        )
        query = pgCursor.fetchall()
        pgCursor.close()
        if not query:
            return {}
        return {
            item[0].split('(')[1].split(')')[0].replace(' ', '') :
            item[0].split('(')[1].split('.')[1]
            for item in query
        }

    def getAttributeValueMap(self, layerName, layerSchema):        
        domains = self.getLayerDomains(layerName, layerSchema)
        fieldsValueMap = []        
        pgCursor = self.getConnection().cursor()
        for fieldName in domains:
            contrains = self.getLayerContrainsCodes(layerName)
            pgCursor.execute(
                "SELECT code, code_name FROM {0}.{1} {2};".format(
                    'dominios', 
                    domains[fieldName], 
                    'WHERE code IN ({0})'.format(contrains[fieldName]) if fieldName in contrains else ''
                )
            )
            query = pgCursor.fetchall()
            if not query:
                continue
            fieldsValueMap.append({
                'attribute': fieldName,
                'valueMap': {v : k for k, v in dict(query).items()}
            })
        pgCursor.close()
        return fieldsValueMap
        
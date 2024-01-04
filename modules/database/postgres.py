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
            f"""select distinct case
                    when split_part(conrelid::regclass::text,'.',2) = '' then split_part(conrelid::regclass::text,'.',1)
                    else split_part(conrelid::regclass::text,'.',2)
                    end as cl, pg_get_constraintdef(oid) 
                FROM
                    pg_constraint WHERE contype = 'c' and case
                    when split_part(conrelid::regclass::text,'.',2) = '' then split_part(conrelid::regclass::text,'.',1)
                    else split_part(conrelid::regclass::text,'.',2)
                    end in ('{layerName}')"""
        )
        query = pgCursor.fetchall()
        pgCursor.close()
        if not query:
            return {}
        result = {}
        for cl, constraintDef in query:
            if not(cl and constraintDef):
                return {}
            tableName, field, codeList = self.parseCheckConstraintQuery(cl, constraintDef)
            result[field] = ",".join(map(str,codeList))
        return result
    
    def parseCheckConstraintQuery(self, queryValue0, queryValue1):
        try:
            if "ANY" in queryValue1 or "@" in queryValue1:
                return self.parseCheckConstraintWithAny(queryValue0, queryValue1)
            else:
                return self.parseCheckConstraintWithOr(queryValue0, queryValue1)
        except Exception as e:
            raise Exception(
                self.tr("Error parsing check constraint!\n" + ":".join(e.args))
            )

    def parseCheckConstraintWithOr(self, queryValue0, queryValue1):
        if "." in queryValue0:
            query0Split = queryValue0.split(".")
            tableSchema = query0Split[0]
            tableName = query0Split[1]
        else:
            tableName = queryValue0
        query1Split = (
            queryValue1.replace("CHECK ", "")
            .replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace('"', "")
            .split("OR")
        )
        checkList = []
        for i in query1Split:
            attrSplit = i.split("=")
            attribute = attrSplit[0]
            try:
                checkList.append(int(attrSplit[1]))
            except:
                pass  # ignore checks that are not from dsgtools
        return tableName, attribute, checkList

    def parseCheckConstraintWithAny(self, queryValue0, queryValue1):
        if "." in queryValue0:
            query0Split = queryValue0.split(".")
            tableSchema = query0Split[0]
            tableName = query0Split[1]
        else:
            tableName = queryValue0
        query1Split = (
            queryValue1.replace('"', "")
            .replace("ANY", "")
            .replace("ARRAY", "")
            .replace("::smallint", "")
            .replace("(", "")
            .replace(")", "")
            .replace("CHECK", "")
            .replace("[", "")
            .replace("]", "")
            .replace(" ", "")
        )
        checkList = []
        splitToken = ""
        if "=" in query1Split:
            splitToken = "="
        elif "<@" in query1Split:
            splitToken = "<@"
        equalSplit = query1Split.split(splitToken)
        attribute = equalSplit[0]
        checkList = list(map(int, equalSplit[1].split(",")))
        return tableName, attribute, checkList

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
        
from Ferramentas_Producao.modules.database.postgres import Postgres


class DatabaseFactory:

    def __init__(self):
        super(DatabaseFactory, self).__init__()

    def createPostgres(self, 
            dbName, 
            dbHost, 
            dbPort, 
            dbUser, 
            dbPassword
        ):
        return Postgres(
            dbName, 
            dbHost, 
            dbPort, 
            dbUser, 
            dbPassword
        )
            
from SAP_Operador.modules.sap.api.sapPostgres import SapPostgres

class SapApiPostgresSingleton:

    sapApi = None

    @staticmethod
    def getInstance():
        if not SapApiPostgresSingleton.sapApi:
            SapApiPostgresSingleton.sapApi = SapPostgres()
            return SapApiPostgresSingleton.sapApi
        return SapApiPostgresSingleton.sapApi
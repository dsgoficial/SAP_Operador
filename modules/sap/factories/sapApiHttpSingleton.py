from SAP_Operador.modules.sap.api.sapHttp import SapHttp

class SapApiHttpSingleton:

    sapApi = None

    @staticmethod
    def getInstance():
        if not SapApiHttpSingleton.sapApi:
            SapApiHttpSingleton.sapApi = SapHttp()
            return SapApiHttpSingleton.sapApi
        return SapApiHttpSingleton.sapApi
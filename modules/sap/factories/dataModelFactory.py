from Ferramentas_Producao.modules.sap.dataModels.sapActivityHttp import SapActivityHttp
from Ferramentas_Producao.modules.sap.dataModels.sapActivityPostgres import SapActivityPostgres

class DataModelFactory:

    def createDataModel(self, modelName):
        dataModels = {
            'SapActivityHttp': SapActivityHttp,
            'SapActivityPostgres': SapActivityPostgres
        }
        return dataModels[modelName]()
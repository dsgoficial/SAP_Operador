from Ferramentas_Producao.modules.sap.dataModels.sapActivityHttp import SapActivityHttp
from Ferramentas_Producao.modules.sap.dataModels.sapActivityLocal import SapActivityLocal

class DataModelFactory:

    def createDataModel(self, modelName):
        dataModels = {
            'SapActivityHttp': SapActivityHttp,
            'SapActivityLocal': SapActivityLocal
        }
        return dataModels[modelName]()
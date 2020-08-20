from Ferramentas_Producao.modules.sap.dataModels.sapActivity import SapActivity

class DataModelFactory:

    def createDataModel(modelName):
        dataModels = {
            'SapActivity': SapActivity
        }
        return dataModels[modelName]()
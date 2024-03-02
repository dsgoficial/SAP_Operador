from SAP_Operador.modules.qgis.factories.fpProcessingProviderSingleton import FPProcessingProviderSingleton

class ProcessingProviderFactory:

    def createProvider(self, typeName):
        typeNames = {
            'SAP_Operador': FPProcessingProviderSingleton
        }
        return typeNames[typeName].getInstance()
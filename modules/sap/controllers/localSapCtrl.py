from Ferramentas_Producao.modules.sap.controllers.sapCtrl import SapCtrl
from Ferramentas_Producao.modules.sap.factories.sapApiPostgresSingleton import SapApiPostgresSingleton
from Ferramentas_Producao.modules.sap.factories.dataModelFactory import DataModelFactory
from Ferramentas_Producao.modules.sap.factories.guiFactory import GUIFactory
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

class LocalSapCtrl(SapCtrl):
    
    def __init__(self, 
            qgis,
            messageFactory=UtilsFactory().createMessageFactory(),
            sapApi=SapApiPostgresSingleton.getInstance(),
            dataModelFactory=DataModelFactory(),
            guiFactory=GUIFactory()
        ):
        super(LocalSapCtrl, self).__init__()
        self.qgis = qgis
        self.messageFactory = messageFactory
        self.dataModelFactory = dataModelFactory
        self.sapApi = sapApi
        self.guiFactory = guiFactory
        self.activityDataModel = self.dataModelFactory.createDataModel('SapActivityPostgres')

    def authUser(self, dbusername, dbpassword, dbhost, dbport, dbname):
        self.sapApi.setConnection(dbusername, dbpassword, dbhost, dbport, dbname)

    def getActivity(self):
        self.activityDataModel.setData(self.sapApi.getActivity())
        return self.activityDataModel
        
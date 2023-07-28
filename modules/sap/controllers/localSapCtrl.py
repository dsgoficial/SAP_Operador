from Ferramentas_Producao.modules.sap.controllers.sapCtrl import SapCtrl
from Ferramentas_Producao.modules.sap.factories.sapApiHttpSingleton import SapApiHttpSingleton
from Ferramentas_Producao.modules.sap.factories.dataModelFactory import DataModelFactory
from Ferramentas_Producao.modules.sap.factories.guiFactory import GUIFactory
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory
from PyQt5 import QtCore, uic, QtWidgets

class LocalSapCtrl(SapCtrl):

    def __init__(self, 
            qgis,
            messageFactory=UtilsFactory().createMessageFactory(),
            sapApi=SapApiHttpSingleton.getInstance(),
            dataModelFactory=DataModelFactory(),
            guiFactory=GUIFactory()
        ):
        super(LocalSapCtrl, self).__init__()
        self.qgis = qgis
        self.reportErrorDialog = None
        self.messageFactory = messageFactory
        self.dataModelFactory = dataModelFactory
        self.sapApi = sapApi
        self.guiFactory = guiFactory
        self.activityDataModel = self.dataModelFactory.createDataModel('SapActivityLocal')

    def getActivity(self, activityData):
        self.activityDataModel.setData( activityData ) 
        return self.activityDataModel
        


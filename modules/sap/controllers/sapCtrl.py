from SAP_Operador.modules.sap.interfaces.ISapCtrl import ISapCtrl
from SAP_Operador.modules.sap.factories.sapApiPostgresSingleton import SapApiPostgresSingleton
from SAP_Operador.modules.sap.factories.dataModelFactory import DataModelFactory
from SAP_Operador.modules.sap.factories.guiFactory import GUIFactory

class SapCtrl(ISapCtrl):
    
    def __init__(self):
        super(SapCtrl, self).__init__()

    def showErrorMessageBox(self, parent, title, message):
        errorMessageBox = self.messageFactory.createMessage('ErrorMessageBox')
        errorMessageBox.show(parent, title, message)

    def showQuestionMessageBox(self, parent, title, message):
        questionMessageBox = self.messageFactory.createMessage('QuestionMessageBox')
        return questionMessageBox.show(parent, title, message)
    
    def showInfoMessageBox(self, parent, title, message):
        infoMessageBox = self.messageFactory.createMessage('InfoMessageBox')
        infoMessageBox.show(parent, title, message)
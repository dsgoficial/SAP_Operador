from Ferramentas_Producao.modules.sap.interfaces.ISapCtrl import ISapCtrl

from Ferramentas_Producao.modules.sap.factories.sapApiSingleton import SapApiSingleton
from Ferramentas_Producao.modules.sap.factories.dataModelFactory import DataModelFactory

from Ferramentas_Producao.modules.sap.factories.guiFactory import GUIFactory

class SapCtrl(ISapCtrl):
    
    def __init__(self, 
            qgis,
            messageFactory,
            sapApi=SapApiSingleton.getInstance(),
            dataModelFactory=DataModelFactory,
            guiFactory=GUIFactory()
        ):
        super(SapCtrl, self).__init__()
        self.qgis = qgis
        self.messageFactory = messageFactory
        self.activityDataModel = dataModelFactory.createDataModel('SapActivity')
        self.sapApi = sapApi
        self.guiFactory = guiFactory
        self.loginDialog = self.guiFactory.createLoginDialog(self)
        self.loginDialog.setController(self)

    def login(self):
        self.loginDialog.loadData(
            user=self.qgis.getSettingsVariable('productiontools:user'), 
            server=self.qgis.getSettingsVariable('productiontools:server'),
            password=self.qgis.getSettingsVariable('productiontools:password')
        )
        return self.loginDialog.showView()

    def saveLoginData(self, user, password, server):
        self.qgis.setSettingsVariable('productiontools:user', user)
        self.qgis.setSettingsVariable('productiontools:password', password)
        self.qgis.setSettingsVariable('productiontools:server', server)

    def authUser(self, user, password, server):
        self.sapApi.setServer(server)
        response = self.sapApi.loginAdminUser(
            user, 
            password,
            self.qgis.getVersion(),
            self.qgis.getPluginsVersions()
        )
        return response['success']

    def showErrorMessageBox(self, parent, title, message):
        errorMessageBox = self.messageFactory.createErrorMessageBox()
        errorMessageBox.show(parent, title, message)

    def showQuestionMessageBox(self, parent, title, message):
        questionMessageBox = self.messageFactory.createQuestionMessageBox()
        questionMessageBox.show(parent, title, message)
    
    def showInfoMessageBox(self, parent, title, message):
        infoMessageBox = self.messageFactory.createInfoMessageBox()
        infoMessageBox.show(parent, title, message)

    def getCurrentActivity(self):
        response = self.sapApi.getActivity()
        if not( 'dados' in response and response['dados'] ):
            self.showErrorMessageBox(
                self.qgis.getMainWindow(),
                'Aviso',
                response['message']
            )
            return None
        response['usuario'] = self.qgis.getSettingsVariable('productiontools:user')
        response['senha'] = self.qgis.getSettingsVariable('productiontools:password')
        return response

    def initActivity(self):
        if not self.showQuestionMessageBox(
                self.qgis.getMainWindow(),
                'Atenção',
                '<p>Deseja iniciar a próxima atividade?</p>'
            ):
            return None
        response = self.sapApi.initActivity()
        if not( response['success'] and 'dados' in response and response['dados'] ):
            self.showErrorMessageBox(
                self.qgis.getMainWindow(),
                'Aviso',
                response['message']
            )
            return None
        return response

    def getActivity(self):
        response = self.getCurrentActivity()
        if response:   
            self.activityDataModel.setData(response)
            return self.activityDataModel
        response = self.initActivity()
        if response:
            self.activityDataModel.setData(response)
            return self.activityDataModel
        self.showInfoMessageBox(
            self.qgis.getMainWindow(),
            'Aviso',
            '''<p>Não há nenhum trabalho cadastrado para você.
                </p><p>Procure seu chefe de seção.</p>'''
        )
        return None

    def endActivity(self, activityId, withoutCorrection):
        return self.sapApi.endActivity(activityId, withoutCorrection)

    def getErrorsTypes(self):
        response = self.sapApi.getErrorsTypes()
        if not( 'dados' in response ):
            return []
        return response['dados']
    
    def showReportErrorDialog(self, callback):
        reportErrorDialog = self.guiFactory.createReportErrorDialog(self)
        reportErrorDialog.loadErrorsTypes(
            self.getErrorsTypes()
        )
        reportErrorDialog.exec_()
        callback()

    def showEndActivityDialog(self, callback):
        endActivityDialog = self.guiFactory.createEndActivityDialog(self)
        endActivityDialog.setController(sender)
        endActivityDialog.exec_()
        callback()
        
    def reportError(self, errorId, errorDescription):
        return self.sapApi.reportError(errorId, errorDescription)
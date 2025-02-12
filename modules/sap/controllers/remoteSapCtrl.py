from SAP_Operador.modules.sap.controllers.sapCtrl import SapCtrl
from SAP_Operador.modules.sap.factories.sapApiHttpSingleton import SapApiHttpSingleton
from SAP_Operador.modules.sap.factories.dataModelFactory import DataModelFactory
from SAP_Operador.modules.sap.factories.guiFactory import GUIFactory
from SAP_Operador.modules.utils.factories.utilsFactory import UtilsFactory
from PyQt5 import QtCore, uic, QtWidgets

class RemoteSapCtrl(SapCtrl):
    
    def __init__(self, 
            qgis,
            messageFactory=None,
            sapApi=None,
            dataModelFactory=None,
            guiFactory=None,
        ):
        super(RemoteSapCtrl, self).__init__()
        self.qgis = qgis
        self.reportErrorDialog = None
        self.messageFactory = UtilsFactory().createMessageFactory() if messageFactory is None else messageFactory
        self.dataModelFactory = DataModelFactory() if dataModelFactory is None else dataModelFactory
        self.sapApi = SapApiHttpSingleton.getInstance() if sapApi is None else sapApi
        self.guiFactory = GUIFactory() if guiFactory is None else guiFactory
        self.activityDataModel = self.dataModelFactory.createDataModel('SapActivityHttp')

    def setupActivityDataModel(self, data):
        if not('login' in data):
            data['login'] = self.qgis.getProjectVariable('productiontools:user')
        if not('senha' in data):
            data['senha'] = self.qgis.getProjectVariable('productiontools:password')
        self.activityDataModel.setData( data ) 

    def setupActivityDataModelExternally(self, data):
        self.activityDataModel.setData( data ) 

    def getActivityDataModel(self):
        return self.activityDataModel

    def showErrorMessageBox(self, parent, title, message):
        parent = self.qgis.getMainWindow() if not parent else parent
        errorMessageBox = self.messageFactory.createMessage('ErrorMessageBox')
        errorMessageBox.show(parent, title, message)

    def showQuestionMessageBox(self, parent, title, message):
        parent = self.qgis.getMainWindow() if not parent else parent
        questionMessageBox = self.messageFactory.createMessage('QuestionMessageBox')
        return questionMessageBox.show(parent, title, message)
    
    def showInfoMessageBox(self, parent, title, message):
        parent = self.qgis.getMainWindow() if not parent else parent
        infoMessageBox = self.messageFactory.createMessage('InfoMessageBox')
        infoMessageBox.show(parent, title, message)    
        
    def authUser(self, user, password, server):
        response = self.sapApi.loginUser(
            user, 
            password,
            self.qgis.getVersion(),
            self.qgis.getPluginsVersions()
        )
        return response['success']

    def setServer(self, server):
        self.sapApi.setServer(server)

    def reAuthUser(self):
        user = self.qgis.getProjectVariable('productiontools:user')
        password = self.qgis.getProjectVariable('productiontools:password')
        server = self.qgis.getSettingsVariable('productiontools:server')
        if not(user and password and server):
            return
        self.authUser(user, password, server)

    def initActivity(self):
        response = self.sapApi.initActivity()
        if not( response['success'] and 'dados' in response and response['dados'] ):
            self.showErrorMessageBox(
                self.qgis.getMainWindow(),
                'Aviso',
                response['message']
            )
            return None
        return response

    def getUserName(self):
        return self.activityDataModel.getUserName()

    def getActivity(self):
        response = self.sapApi.getActivity()
        if 'dados' in response and response['dados']:  
            self.setupActivityDataModel(response)
            #self.activityDataModel.setData(response)
            self.qgis.setProjectVariable(
                'productiontools:activityName', 
                self.activityDataModel.getDescription()
            )
            return self.activityDataModel
        if not self.showQuestionMessageBox(
                self.qgis.getMainWindow(),
                'Atenção',
                '<p>Deseja iniciar a próxima atividade?</p>'
            ):
            return None
        response = self.initActivity()
        if response:
            self.setupActivityDataModel(response)
            #self.activityDataModel.setData(response)
            return self.activityDataModel
        self.showInfoMessageBox(
            self.qgis.getMainWindow(),
            'Aviso',
            '''<p>Não há nenhum trabalho cadastrado para você.
                </p><p>Procure seu chefe de seção.</p>'''
        )
        

    def getCurrentActivity(self):
        response = self.sapApi.getActivity()
        if not( 'dados' in response and response['dados'] ):
            self.showErrorMessageBox(
                self.qgis.getMainWindow(),
                'Aviso',
                response['message']
            )
            return None
        #response['usuario'] = self.qgis.getProjectVariable('productiontools:user')
        #response['senha'] = self.qgis.getProjectVariable('productiontools:password')
        return response

    def endActivity(self, data):
        return self.sapApi.endActivity(data)

    def getErrorsTypes(self):
        response = self.sapApi.getErrorsTypes()
        if not( 'dados' in response ):
            return []
        return response['dados']
    
    def showReportErrorDialog(self, callback):
        if self.reportErrorDialog:
            self.reportErrorDialog.close()
        self.reportErrorDialog = self.guiFactory.createReportErrorDialog(
            self,
            self.qgis
        )
        self.reportErrorDialog.loadErrorsTypes(
            self.getErrorsTypes()
        )
        self.reportErrorDialog.reported.connect(callback)
        return self.reportErrorDialog.show()

    #mostrar nova parte apenas quando etapaId 2 e 5
    def showEndActivityDialog(self, withoutCorrection, stepTypeId):
        activeObs = stepTypeId in [2,5]
        endActivityDialog = self.guiFactory.createEndActivityDialog(self, activeObs)
        endActivityDialog.setWithoutCorrection(withoutCorrection)
        return endActivityDialog.exec_() == QtWidgets.QDialog.Accepted
        
    def reportError(self, errorId, errorDescription, wkt):
        return self.sapApi.reportError(self.activityDataModel.getId(),  errorId, errorDescription, wkt)

    def hasActivityRecord(self):
        return (
            self.qgis.getProjectVariable('productiontools:user')
            and
            self.qgis.getSettingsVariable('productiontools:server')
            and
            self.qgis.getProjectVariable('productiontools:password')
            and
            self.qgis.getProjectVariable('productiontools:activityName')
        )

    def hasValidAuthentication(self):
        return self.authUser(
            self.qgis.getProjectVariable('productiontools:user'),
            self.qgis.getProjectVariable('productiontools:password'),
            self.qgis.getSettingsVariable('productiontools:server')
        )

    def isValidActivity(self):
        response = self.getCurrentActivity()
        if not response:
            return True   
        self.setupActivityDataModel(response)
        return self.qgis.getProjectVariable('productiontools:activityName') == self.activityDataModel.getDescription()

    def incorrectEnding(self, description):
        return self.sapApi.incorrectEnding(description)

    def getRemotePluginsPath(self):
        return self.sapApi.getRemotePluginsPath()
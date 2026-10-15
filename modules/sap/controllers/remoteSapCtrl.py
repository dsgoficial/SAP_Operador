from SAP_Operador.modules.sap.controllers.sapCtrl import SapCtrl
from SAP_Operador.modules.sap.factories.sapApiHttpSingleton import SapApiHttpSingleton
from SAP_Operador.modules.sap.factories.dataModelFactory import DataModelFactory
from SAP_Operador.modules.sap.factories.guiFactory import GUIFactory
from SAP_Operador.modules.utils.factories.utilsFactory import UtilsFactory
from SAP_Operador.modules.sap.api.sapHttp import VersioningConflict
from qgis.PyQt import QtCore, uic, QtWidgets

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
        # O login e a senha do SAP não entram mais no pacote: serviam de
        # credencial do banco de produção do tipo 3, que saiu (4.4.0).
        self.activityDataModel.setData( data ) 

    def getUnsupportedReason(self, data):
        # O motivo de recusar o pacote (dado de produção que não é a base
        # versionada, de um servidor antigo), lido num modelo à parte para não
        # trocar o pacote da atividade aberta.
        candidate = self.dataModelFactory.createDataModel('SapActivityHttp')
        candidate.setData(data)
        return candidate.getUnsupportedReason()

    def refuseUnsupportedActivity(self, data):
        # True quando o pacote foi recusado; o operador vê o motivo, e o
        # plugin segue sem atividade aberta.
        reason = self.getUnsupportedReason(data)
        if not reason:
            return False
        self.showErrorMessageBox(
            self.qgis.getMainWindow(),
            'Atividade não atendida',
            '<p>{0}</p>'.format(reason)
        )
        return True

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
            if self.refuseUnsupportedActivity(response):
                return None
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
            if self.refuseUnsupportedActivity(response):
                return None
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
        # Versionado: um 409 com sessao_id abre a tela de conflitos; resolvidos,
        # "Finalizar de novo" chama o finaliza outra vez. Fechar a tela mantém a
        # atividade em execução.
        while True:
            try:
                return self.sapApi.endActivity(data)
            except VersioningConflict as conflict:
                if not self.resolveVersioningConflict(conflict.answer):
                    raise Exception(
                        'A atividade continua em execução: há conflitos de integração a resolver antes de finalizar.'
                    )

    def resolveVersioningConflict(self, answer, parent=None):
        """Abre a tela de conflitos da sessão do 409; True quando o operador pede para finalizar de novo."""
        from SAP_Operador.modules.versionamento import camadas
        from SAP_Operador.modules.versionamento.painel import (
            ConflictDialog, ConflictPayload, SessionResolver, connection_for, session_repository
        )
        payload = ConflictPayload(answer)
        versioning = self.activityDataModel.getVersioning()
        if not (payload.valid and versioning):
            return False
        camadas.conectar(self.sapApi.getServer(), self.sapApi.getToken, self.sapApi._reAuth)
        serviceBase = camadas.base(versioning, self.sapApi.getServer())
        client = connection_for(serviceBase).client
        repo = session_repository(client, versioning['repo_id'], payload)
        self.conflictDialog = ConflictDialog(
            parent or self.qgis.getMainWindow(),
            SessionResolver(client, repo, payload.session),
            payload
        )
        return self.conflictDialog.exec() == QtWidgets.QDialog.DialogCode.Accepted

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
        activeObs = stepTypeId in [2, 4, 5]
        endActivityDialog = self.guiFactory.createEndActivityDialog(self, activeObs, stepTypeId)
        endActivityDialog.setWithoutCorrection(withoutCorrection)
        return endActivityDialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
        
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
        if self.refuseUnsupportedActivity(response):
            return False
        self.setupActivityDataModel(response)
        return self.qgis.getProjectVariable('productiontools:activityName') == self.activityDataModel.getDescription()

    def incorrectEnding(self, description):
        return self.sapApi.incorrectEnding(description)

    def getRemotePluginsPath(self):
        return self.sapApi.getRemotePluginsPath()

    def getKeywordTypes(self):
        response = self.sapApi.getKeywordTypes()
        if not ('dados' in response):
            return []
        return response['dados']

    def saveEditionMetadata(self, metadados):
        return self.sapApi.saveEditionMetadata(metadados)

    def getEditionJson(self, versaoUuid):
        response = self.sapApi.getEditionJson(versaoUuid)
        if not ('dados' in response):
            return {}
        return response['dados']
# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QSettings
import json, sys, os, copy, base64
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from managerQgis.projectQgis import ProjectQgis
from managerNetwork.network import Network

#carrega o arquivo da interface .ui
sys.path.append(os.path.dirname(__file__))
GUI, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__),
    u"ui",
    u"login_interface.ui"), 
    resource_suffix=''
) 

class Login(QtGui.QDialog, GUI):
    
    showTools = QtCore.pyqtSignal(dict)

    def __init__(self, iface):
        super(Login, self).__init__()
        self.setupUi(self)
        self.iface = iface
        self.loadFields()
        self.version_lb.setText(u"<b>versão : 2.18.4</b>")
        self.connectionTypeSlider.valueChanged.connect(
            self.connectionType
        )
    
    def encrypt(self, key, plaintext):
        return base64.b64encode(plaintext)

    def decrypt(self, key, ciphertext):
        return base64.b64decode(ciphertext)

    def loadFields(self):
        self.projectQgis = ProjectQgis(self.iface)
        settings = QSettings()
        settings.beginGroup('SAP/server')
        server = settings.value('server')
        settings.endGroup()
        if server:
            self.serverLineEdit.setText(server)
        user = self.projectQgis.getVariableProject('usuario')
        password = self.projectQgis.getVariableProject('senha')
        if user and password:
            self.nameLineEdit.setText(self.decrypt('123456', user))
            self.passwordLineEdit.setText(self.decrypt('123456', password))
   
    def connectionType(self, value):
        if value == 0:
            self.dataFrame.setEnabled(True)
        else:
            self.dataFrame.setEnabled(False) 

    def message(self, msgTitle, msg):
        QtGui.QMessageBox.critical(
                self,
                msgTitle, 
                msg
        ) 

    @QtCore.pyqtSlot(bool)
    def on_okPushButton_clicked(self, b):
        connectionValue = self.connectionTypeSlider.value()
        if connectionValue == 1:
            self.loginLocal()
        else:
            self.loginRemote()
            
    @QtCore.pyqtSlot(bool)
    def on_cancelPushButton_clicked(self, b):
        self.reject()

    def loginLocal(self):
        self.accept()
        self.showTools.emit({})

    def loginRemote(self, user=False, password=False, server=False):
        if (server and user and password) or (self.serverLineEdit.text() and self.nameLineEdit.text() and self.passwordLineEdit.text()):
            server = self.serverLineEdit.text()
            user = self.nameLineEdit.text()
            password = self.passwordLineEdit.text()
            data, status_code = self.checkLogin(server, user, password)
            if (status_code == 500):
                QtGui.QMessageBox.critical(
                    self,
                    u"Erro", 
                    u"Status : <p>Erro no servidor!</p>"
                )
            elif (status_code in [401, 403]):
                QtGui.QMessageBox.critical(
                    self,
                    u"Erro", 
                    u"Status : <p>Usuário ou senha incorretos!</p>"
                )
            elif (status_code == 1):
                QtGui.QMessageBox.critical(
                    self,
                    u"Erro", 
                    u"Status : <p>Erro no POST!</p>"
                )
            elif (status_code == 2):
                QtGui.QMessageBox.critical(
                    self,
                    u"Erro", 
                    u"Status : <p>Erro de conexão. verifique se o IP do servidor está correto!</p>"
                )
            elif "dados" in data:
                self.init_tools(data, user, password, server)
                return data
            elif not("dados" in data):
                result = QtGui.QMessageBox().question(
                    self,
                    u"AVISO!", 
                    u"Deseja iniciar a próxima atividade?",
                    buttons=QtGui.QMessageBox.No|QtGui.QMessageBox.Ok
                )
                if result == 1024:
                    data = self.initActivity(server, data['token'])
                    if "dados" in data:
                        self.init_tools(data, user, password, server)
                        return data
                    QtGui.QMessageBox.information(
                        self,
                        u"Aviso!", 
                        u"Status : <p>Não há nenhum trabalho cadastrado para você.</p><p>Procure seu chefe de seção.</p>"
                    )
    
    def init_tools(self, data, user, password, server):
        data[u"connectionType"] = u"remote"
        data[u"user"] = user
        data[u"password"] = password
        data["server"] = server
        data[u"ok"] = True
        data_encode =  data['dados']['atividade']['nome'].encode('utf-8')
        settings = QSettings()
        settings.beginGroup('SAP/server')
        settings.setValue('server', server)
        settings.endGroup()
        self.projectQgis.setProjectVariable('usuario', self.encrypt('123456', user))
        self.projectQgis.setProjectVariable('senha', self.encrypt('123456', password))
        self.projectQgis.setProjectVariable('atividade', self.encrypt('123456', data_encode))
        self.accept()
        self.showTools.emit(data)
                    
    def initActivity(self, server, token):
        header = {'authorization' : token}
        url = u"{0}/distribuicao/inicia".format(server)
        response = Network().POST(server, url, header=header)
        data = response.json()
        if data["sucess"]:
            data['token'] = token
            return data

    def finishActivity(self, server, unitId, faseId, token):
        postData = {
            "subfase_etapa_id" : faseId,
            "unidade_trabalho_id" : unitId,
        }
        header = {'authorization' : token}
        url = u"{0}/distribuicao/finaliza".format(server)
        response = Network().POST(server, url, postData, header)
        return response.status_code

    def checkLogin(self, server, user, password):
        if Network().server_on(server):
            try:
                postData = { 
                    u"usuario" : user,
                    u"senha" : password
                }
                url = u"{0}/login".format(server)
                response = Network().POST(server, url, postData)
                if response.json()["sucess"]:
                    token = response.json()["dados"]["token"]
                    header = {'authorization' : token}
                    url = u"{0}/distribuicao/verifica".format(server)
                    response = Network().GET(server, url, header)
                    data = response.json()
                    print data
                    data['token'] = token
                    return data, response.status_code
                return False, response.status_code
            except Exception as e:
                print e
                return False, 1
        return False, 2
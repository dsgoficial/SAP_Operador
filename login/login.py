# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
import sys, os
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
        self.version_lb.setText(u"<b>versão : 2.13.0</b>")
        self.connectionTypeSlider.valueChanged.connect(
            self.connectionType
        )
    
    def loadFields(self):
        self.serverLineEdit.setText("http://10.25.163.42:3013")
        self.projectQgis = ProjectQgis(self.iface)
        usuario = self.projectQgis.getVariableProject('usuario')
        senha = self.projectQgis.getVariableProject('senha')
        if usuario and senha:
            self.nameLineEdit.setText(usuario)
            self.passwordLineEdit.setText(senha)
   
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
        if not(server):
            server = self.serverLineEdit.text()
        if not(user):
            user = self.nameLineEdit.text()
        if not(password):
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
            data[u"connectionType"] = u"remote"
            data[u"user"] = user
            data[u"password"] = password
            data["server"] = server
            data[u"ok"] = True
            self.projectQgis.setProjectVariable('usuario', user)
            self.projectQgis.setProjectVariable('senha', password)
            self.accept()
            self.showTools.emit(data)
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
                    data[u"connectionType"] = u"remote"
                    data[u"user"] = user
                    data[u"password"] = password
                    data["server"] = server
                    data[u"ok"] = True
                    self.projectQgis.setProjectVariable('usuario', user)
                    self.projectQgis.setProjectVariable('senha', password)
                    self.accept()
                    self.showTools.emit(data)
                    return data
                QtGui.QMessageBox.information(
                    self,
                    u"Aviso!", 
                    u"Status : <p>Não há nenhum trabalho cadastrado para você.</p><p>Procure seu chefe de seção.</p>"
                )
                
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
                    data['token'] = token
                    return data, response.status_code
                return False, response.status_code
            except:
                return False, 1
        return False, 2

    
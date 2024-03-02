import json, requests, socket

from SAP_Operador.modules.sap.interfaces.ISapApi import ISapApi

TIMEOUT = 60 * 3

class SapHttp(ISapApi):   

    def __init__(self):
        super(SapHttp, self).__init__()
        self.server = None
        self.token = None

    def httpPost(self, url, postData, headers):
        if self.getToken():
            headers['authorization'] = self.getToken()
        session = requests.Session()
        session.trust_env = False
        response = session.post(url, data=json.dumps(postData), headers=headers, timeout=TIMEOUT)
        self.checkError(response)
        return response

    def httpGet(self, url): 
        headers = {}
        if self.getToken():
            headers['authorization'] = self.getToken()
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, headers=headers, timeout=TIMEOUT)
        self.checkError(response)
        return response

    def httpPut(self, url, postData={}, headers={}):
        if self.getToken():
            headers['authorization'] = self.getToken()
        session = requests.Session()
        session.trust_env = False
        response = session.put(url, data=json.dumps(postData), headers=headers, timeout=TIMEOUT)
        self.checkError(response)
        return response

    def httpDelete(self, url, postData={}, headers={}):
        if self.getToken():
            headers['authorization'] = self.getToken()
        session = requests.Session()
        session.trust_env = False
        response = session.delete(url, data=json.dumps(postData), headers=headers, timeout=TIMEOUT)
        self.checkError(response)
        return response

    def setServer(self, server):
        self.server = "{0}/api".format(server)

    def getServer(self):
        return self.server

    def setToken(self, token):
        self.token = token

    def getToken(self):
        return self.token
    
    def loginUser(self, user, password, gisVersion, pluginsVersion):
        response = self.httpPostJson(
            url="{0}/login".format(self.getServer()), 
            postData={
                "usuario" : user,
                "senha" : password,
                'plugins' : pluginsVersion,
                'qgis' : gisVersion,
                'cliente' : 'sap_fp'
            }
        )
        responseJson = response.json()
        if not self.validVersion(responseJson):
            raise Exception("Versão do servidor sap errada")
        self.setToken(responseJson['dados']['token'])
        return responseJson

    def validVersion(self, responseJson):
        return ('version' in responseJson and responseJson['version'].split('.')[0] == '2')

    def httpPostJson(self, url, postData):
        headers = {
            'content-type' : 'application/json'
        }
        return  self.httpPost(
            url, 
            postData,
            headers
        )

    def checkError(self, response):
        if response.status_code == 404:
            raise Exception('Servidor não encontrado!')
        if response.status_code == 413:
            raise Exception('Request Entity Too Large!')
        if response.status_code == 504:
            raise Exception('Tempo excedido!')
        if response.status_code == 403:
            raise Exception('Token expirado, faça o login novamente!')
        if not response.ok:
            raise Exception(response.json()['message'])

    def httpPutJson(self, url, postData):
        headers = {
            'content-type' : 'application/json'
        }
        return  self.httpPut(
            url, 
            postData,
            headers
        )

    def httpDeleteJson(self, url, postData):
        headers = {
            'content-type' : 'application/json'
        }
        return  self.httpDelete(
            url, 
            postData,
            headers
        )

    def getActivity(self):
        response = self.httpGet(
            url="{0}/distribuicao/verifica".format(self.getServer())
        )
        if response:
            return response.json()
        return {}

    def initActivity(self):
        response = self.httpPostJson(
            url="{0}/distribuicao/inicia".format(self.getServer()),
            postData={}
        )
        if response:
            return response.json()
        return {}

    def endActivity(self, data):
        response = self.httpPostJson(
            url="{0}/distribuicao/finaliza".format(self.getServer()),
            postData=data
        )
        return response.json()['message']

    def reportError(self, activityId, errorId, errorDescription, wkt):
        response = self.httpPostJson(
            url="{0}/distribuicao/problema_atividade".format(self.getServer()),
            postData={
                'atividade_id' : activityId,
                'tipo_problema_id' : errorId,
                'descricao' : errorDescription,
                'polygon_ewkt': wkt
            }
        )
        return response.json()['message']

    def getErrorsTypes(self):
        response = self.httpGet(
            url="{0}/distribuicao/tipo_problema".format(self.getServer())
        )
        if response:
            return response.json()
        return {}

    def incorrectEnding(self, description):
        response = self.httpPostJson(
            url="{0}/distribuicao/finalizacao_incorreta".format(self.getServer()),
            postData={
                'descricao' : description
            }
        )
        return response.json()['message']

    def getRemotePluginsPath(self):
        response = self.httpGet(
            url="{0}/distribuicao/plugin_path".format(self.getServer())
        )
        if response:
            return response.json()
        return {}
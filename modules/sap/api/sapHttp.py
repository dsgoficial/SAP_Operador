import json, requests, socket

from SAP_Operador.modules.sap.interfaces.ISapApi import ISapApi

TIMEOUT = 60 * 3


class VersioningConflict(Exception):
    """409 do `finaliza` de atividade versionada: o merge do clone tem
    conflitos. `answer` é o JSON inteiro da resposta (o contrato diz
    `{ sessao_id, conflitos }`; o envelope do SAP o põe em `dados`)."""
    def __init__(self, message, answer):
        super().__init__(message)
        self.answer = answer

class SapHttp(ISapApi):

    def __init__(self):
        super(SapHttp, self).__init__()
        self.server = None
        self.token = None
        self._loginCredentials = None
        self._isReAuthenticating = False
        self._session = requests.Session()
        self._session.trust_env = False

    def _reAuth(self):
        if not self._loginCredentials:
            return False
        self._isReAuthenticating = True
        try:
            response = self.httpPostJson(
                url="{0}/login".format(self.getServer()),
                postData={
                    "usuario" : self._loginCredentials['user'],
                    "senha" : self._loginCredentials['password'],
                    'plugins' : self._loginCredentials['pluginsVersion'],
                    'qgis' : self._loginCredentials['gisVersion'],
                    'cliente' : 'sap_fp'
                }
            )
            responseJson = response.json()
            if not self.validVersion(responseJson):
                return False
            self.setToken(responseJson['dados']['token'])
            return True
        except Exception:
            return False
        finally:
            self._isReAuthenticating = False

    def _requestWithRetry(self, method, url, **kwargs):
        headers = kwargs.get('headers', {})
        if self.getToken():
            headers['authorization'] = self.getToken()
        kwargs['headers'] = headers
        kwargs['timeout'] = TIMEOUT
        response = getattr(self._session, method)(url, **kwargs)
        # No SAP 3.0 o token vencido responde 401; o 403 é falta de perfil, e
        # refazer o login não o resolve.
        if response.status_code == 401 and not self._isReAuthenticating and self._reAuth():
            kwargs['headers']['authorization'] = self.getToken()
            response = getattr(self._session, method)(url, **kwargs)
        self.checkError(response)
        return response

    def httpPost(self, url, postData, headers):
        return self._requestWithRetry('post', url, data=json.dumps(postData), headers=headers)

    def httpGet(self, url):
        return self._requestWithRetry('get', url, headers={})

    def httpPut(self, url, postData=None, headers=None):
        return self._requestWithRetry('put', url, data=json.dumps(postData or {}), headers=headers or {})

    def httpDelete(self, url, postData=None, headers=None):
        return self._requestWithRetry('delete', url, data=json.dumps(postData or {}), headers=headers or {})

    def setServer(self, server):
        self.server = "{0}/api".format(server)

    def getServer(self):
        return self.server

    def setToken(self, token):
        self.token = token

    def getToken(self):
        return self.token
    
    def loginUser(self, user, password, gisVersion, pluginsVersion):
        self._loginCredentials = {
            'user': user,
            'password': password,
            'gisVersion': gisVersion,
            'pluginsVersion': pluginsVersion
        }
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
            raise Exception("Versão do servidor SAP incompatível: este plugin exige o SAP 3.x.")
        self.setToken(responseJson['dados']['token'])
        return responseJson

    def validVersion(self, responseJson):
        return ('version' in responseJson and responseJson['version'].split('.')[0] == '3')

    def httpPostJson(self, url, postData):
        headers = {
            'content-type' : 'application/json'
        }
        return  self.httpPost(
            url, 
            postData,
            headers
        )

    def _serverMessage(self, response):
        try:
            return response.json()['message']
        except Exception:
            return None

    def checkError(self, response):
        if response.status_code == 413:
            raise Exception('Request Entity Too Large!')
        if response.status_code == 504:
            raise Exception('Tempo excedido!')
        if response.status_code == 401:
            raise Exception('Sessão expirada, faça o login novamente!')
        if response.ok:
            return
        if response.status_code == 409:
            try:
                answer = response.json()
            except Exception:
                answer = None
            if isinstance(answer, dict) and (
                    answer.get('sessao_id') or (isinstance(answer.get('dados'), dict) and answer['dados'].get('sessao_id'))
                ):
                raise VersioningConflict(
                    answer.get('message') or 'A integração da atividade tem conflitos a resolver.',
                    answer
                )
        # O SAP 3.0 responde 404 com mensagem própria (atividade ou versão não
        # encontrada) e 403 quando falta o perfil de operador no módulo de
        # produção: a frase do servidor diz o que houve.
        message = self._serverMessage(response)
        if response.status_code == 404 and not message:
            raise Exception('Servidor não encontrado!')
        raise Exception(message or 'Erro {0} no servidor SAP.'.format(response.status_code))

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

    def saveLayerTrack(self, data):
        response = self.httpPostJson(
            url="{0}/microcontrole/feicao".format(self.getServer()),
            postData=data
        )
        return response.json()['message']

    def saveScreenTrack(self, data):
        response = self.httpPostJson(
            url="{0}/microcontrole/tela".format(self.getServer()),
            postData=data
        )
        return response.json()['message']

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

    def getKeywordTypes(self):
        response = self.httpGet(
            url="{0}/metadados/tipo_palavra_chave".format(self.getServer())
        )
        if response:
            return response.json()
        return {}

    def saveEditionMetadata(self, metadados):
        response = self.httpPostJson(
            url="{0}/distribuicao/metadados_edicao".format(self.getServer()),
            postData={'metadados': metadados}
        )
        return response.json()['message']

    def getEditionJson(self, versaoUuid):
        # No SAP 3.0 o parâmetro da rota é o uuid da VERSÃO (acervo.versao.uuid_versao):
        # o que se publica é a edição, e não a folha.
        response = self.httpGet(
            url="{0}/metadados/json_edicao/produto/{1}".format(self.getServer(), versaoUuid)
        )
        if response:
            return response.json()
        return {}
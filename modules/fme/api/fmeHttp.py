import json, requests, socket

from SAP_Operador.modules.fme.interfaces.IFmeApi import IFmeApi

class FmeHttp(IFmeApi):
    def __init__(self):
        super(FmeHttp, self).__init__()

    def checkError(self, response):
        if not response.ok:
            raise Exception(response.json()['message'])

    def httpGet(self, url):
        headers = {}
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, headers=headers, timeout=8)
        self.checkError(response)
        return response

    def getSapRoutines(self, fmeConfig):
        routineSap = []
        for config in fmeConfig:
            # O pacote do SAP 3.0 traz o gerenciador FME como `url`
            # (qgis.gerenciador_fme.url), e nao como servidor e porta.
            server = u"{0}/api/rotinas".format( config['url'].rstrip('/') )
            cat = u"?ids={0}".format( config['rotina'] )
            url = u"{0}{1}".format( server, cat )
            response = self.httpGet(url)
            if not response:
                continue
            routines = response.json()['dados'][:]
            for routine in routines:
                routine.update({
                    'description': '{0}: \n{1}'.format(routine['rotina'], routine['descricao']),
                    'routineType': 'fme',
                    'server': config['url'].rstrip('/')
                })
            routineSap += routines
        return routineSap
            
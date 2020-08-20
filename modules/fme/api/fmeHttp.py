import json, requests, socket

from Ferramentas_Producao.modules.fme.interfaces.IFmeApi import IFmeApi

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
            server = u"http://{0}:{1}/api".format( config['servidor'], config['porta'] )
            cat = u"&workspace={0}".format( config['rotina'] )
            url = u"{0}/versions?last=true{1}".format( server, cat )
            response = self.httpGet(url)
            if not response:
                continue
            routines = response.json()['data'][:]
            for routine in routines:
                routine.update({
                    'description': routine['workspace_description'],
                    'routineType': 'fme',
                    'server': server
                })
            routineSap += routines
        return routineSap
            
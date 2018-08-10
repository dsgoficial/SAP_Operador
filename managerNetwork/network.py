# -*- coding: utf-8 -*-
from PyQt4 import QtCore
from qgis import core, gui
from platform   import system as system_name
import os, requests, sys, re

class Network:

    def server_on(self, server):
        try:
            os.environ[u"NO_PROXY"] = server
            requests.get(server, timeout=8)
            return True
        except: 
            return False
    
    def POST(self, host, url, post_data={}):
        os.environ[u"NO_PROXY"] = host
        response = requests.post(url, json=post_data)
        return response

    def GET(self, host, url):
        try:
            os.environ['NO_PROXY'] = host
            response = requests.get(url)
            return response
        except requests.exceptions.InvalidURL:
            return 1
        except requests.exceptions.ConnectionError:
            return 2

    def initActivity(self, server, token):
        url = u"{0}/distribuicao/inicia?token={1}".format(server, token)
        response = self.POST(server, url)
        data = response.json()
        if data["sucess"]:
            data['token'] = token
            return data

    def finishActivity(self, server, unitId, faseId, token):
        postData = {
            "subfase_etapa_id" : faseId,
            "unidade_trabalho_id" : unitId,
        }
        url = u"{0}/distribuicao/finaliza?token={1}".format(server, token)
        response = self.POST(server, url, postData)
        return response.status_code

    def checkLogin(self, server, user, password):
        if self.server_on(server):
            try:
                postData = { 
                    u"usuario" : user,
                    u"senha" : password
                }
                url = u"{0}/login".format(server)
                response = self.POST(server, url, postData)
                if response.json()["sucess"]:
                    token = response.json()["dados"]["token"]
                    url = u"{0}/distribuicao/verifica?token={1}".format(server, token)
                    response = self.GET(server, url)
                    data = response.json()
                    data['token'] = token
                    return data, response.status_code
                return False, response.status_code
            except:
                return False, 1
        return False, 2
        
    def download(self, pathOrigin, pathDest):
        if system_name == u"Linux":
            return False
            ''' try:
                import pexpect
                child = pexpect(u"scp pluginsqgis@10.25.163.1:/{0} {1}".format(pathOrigin, pathDest))
                r=child.expect ('password:')
                if r==0:
                    child.sendline('senha')
                child.close()
            except:
                pass '''
        else:
            try:
                command = u"copy {0} {1}".format(
                    pathOrigin,
                    pathDest
                )
                os.popen(command)
                originalName = pathOrigin.split(u"\\")[-1]
                if os.path.exists(u"{0}/{1}".format(pathDest, originalName)):
                    return True
                return False
            except:
                return False
    

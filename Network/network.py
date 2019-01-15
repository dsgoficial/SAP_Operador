# -*- coding: utf-8 -*-
from PyQt5 import QtCore
from qgis import gui, core
from platform import system 
import os, requests, sys, re, subprocess, json
#import samba

class Network(QtCore.QObject):
    def __init__(self, parent=None):
        self.parent

    def server_on(self, server):
        try:
            session = requests.Session()
            session.trust_env = False
            session.get(server, timeout=8)
            return True
        except:
            return False

    def POST(self, host, url, post_data={}, header={}):
        header['content-type'] = 'application/json'
        session = requests.Session()
        session.trust_env = False
        response = session.post(url, data=json.dumps(post_data), headers=header)
        return response

    def GET(self, host, url, header={}):
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.get(url, hearders)
            return response
        except requests.exceptions.ConnectionError:
            return {"_erro" : u"Erro de conexão."}
        except requests.exceptions.invalidURL:
            return {"_erro" : u"Url inválida."}
            

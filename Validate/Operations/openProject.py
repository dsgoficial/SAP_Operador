import os, sys
from PyQt5 import QtCore
from qgis import core, gui
from Ferramentas_Producao.utils.managerQgis import ManagerQgis
from Ferramentas_Producao.utils import msgBox
from Ferramentas_Producao.SAP.managerSAP import ManagerSAP

class OpenProject(QtCore.QObject):
    def __init__(self, iface):
        super(OpenProject, self).__init__()
        self.iface = iface
        self.validate()

    def validate(self):
        m_qgis = ManagerQgis(self.iface)
        user = m_qgis.load_project_var('user')
        password = m_qgis.load_project_var('password')
        works = m_qgis.load_project_var('works')
        if user and password and works:
            server = m_qgis.load_qsettings_var('login/server')
            valid = False
            if server:
                m_sap = ManagerSAP(self.iface)
                data = m_sap.getWork(server, user, password)
                #if data and 'dados' in data and data['dados'] and data['dados']['atividade']['nome'] == works:
                valid = True
            if not(valid):
                core.QgsProject.instance().removeAllMapLayers()
                core.QgsProject.instance().layerTreeRoot().removeAllChildren()
                html = u'''<p style="color:red">
                Esse projeto não pode ser acessado. Carregue um novo projeto.
                </p>'''
                msgBox.show(text=html, title=u"Aviso")
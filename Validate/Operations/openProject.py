import os, sys
from PyQt5 import QtCore
from qgis import core, gui
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils.managerQgis import ManagerQgis
from utils import msgBox
from SAP.managerSAP import ManagerSAP

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
        token = m_qgis.load_project_var('token')
        if user and password and works:
            server = m_qgis.load_qsettings_var('login/server')
            valid = False
            if server:
                m_sap = ManagerSAP(self.iface)
                data = m_sap.get_current_works(server, user, password, token)
                if data and 'dados' in data and data['dados']['atividade']['nome'] == works:
                    valid = True
            if not(valid):
                core.QgsProject.instance().removeAllMapLayers()
                core.QgsProject.instance().layerTreeRoot().removeAllChildren()
                html = u'''<p style="color:red">
                Esse projeto não pode ser acessado. Carregue um novo projeto.
                </p>'''
                msgBox.show(text=html, title=u"Aviso")
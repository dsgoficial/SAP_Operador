# -*- coding: utf-8 -*-
from PyQt5 import QtCore
from .routinesFrame import RoutinesFrame
from .routinesLocal import RoutinesLocal
from .routinesFme import RoutinesFme
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from SAP.managerSAP import ManagerSAP
from utils import managerQgis, network, msgBox

class Routines(QtCore.QObject):

    stop_progress = QtCore.pyqtSignal()

    def __init__(self, iface):
        super(Routines, self).__init__()
        self.iface = iface
        self.server = False 
        self.sap_mode = False
        
    def get_frame(self):
        self.frame = RoutinesFrame(self.iface)
        self.frame.run_routine.connect(
            self.run_routine
        )
        if self.sap_mode:
            self.frame.config_sap_mode()
            self.load_routines()
        else:
            self.frame.load_routines.connect(
                self.load_routines
            )
        return self.frame

    def get_local_routines(self):
        local_routines = {}
        if self.sap_mode:
            sap_data = ManagerSAP().load_data()['dados']['atividade']
            local_routines = sap_data['rotinas']
            description = {
                u"notSimpleGeometry" : u"Identifica geometrias não simples.",
                u"outOfBoundsAngles" : u"Identifica ângulos fora da tolerância.",
                u"invalidGeometry" : u"Identifica geometrias inválidas."
            }
            for name in local_routines:
                local_routines[name]['description'] = description[name]
                local_routines[name]['type_routine'] = 'local'
        return local_routines

    def get_fme_routines(self, server=''):
        data = {}
        if self.sap_mode:
            sap_data = ManagerSAP().load_data()['dados']['atividade']
            if  sap_data['fme']:
                server = sap_data['fme']['servidor']
                cat = sap_data['fme']['categoria']
        else:
            if server:
                managerQgis.save_qsettings_var('FME/server', server)
            else:
                server = managerQgis.load_qsettings_var('FME/server')
        if server:
            url = u"http://{0}/versions?last=true{1}".format(
                server,
                u"&category={0}".format(cat) if cat else ''
            )
            net = network
            net.CONFIG['interface'] = self.frame
            response = net.GET(server, url)
            if response:
                data = server_response.json()['data']
                for r in data:
                    r['description'] = r['workspace_description']
                    r['type_routine'] = 'fme'
        return data

    def load_routines(self, server=''):
        rotines_data = {
            'local' : self.get_local_routines(),
            'fme' : self.get_fme_routines(server)
        }
        self.frame.load(routines_data)
    
    def run_routine(self, routine_data):
        type_routine = outine_data['type_routine']
        if type_routine == 'fme':
            self.routine_selected = RoutinesLocal(self.iface, routine_data)
            self.routine_selected.sap_mode = self.sap_mode
        else:
            self.routine_selected = RoutinesFme(self.iface, routine_data)
        self.routine_selected.run()
        

        
    
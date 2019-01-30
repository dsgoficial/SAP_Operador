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

    def __init__(self, iface):
        super(Routines, self).__init__()
        self.iface = iface
        self.server = False 
        self.sap_mode = False
        self.queue_routines = []
        
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

    def load_routines(self, server=''):
        routinesLocal = RoutinesLocal(self.iface)
        routinesLocal.sap_mode = self.sap_mode
        routinesFme = RoutinesFme(self.iface)
        routinesFme.sap_mode = self.sap_mode
        routines_data = {
            'local' : routinesLocal.get_routines_data(),
            'fme' :  routinesFme.get_routines_data(server)
        }
        self.frame.load(routines_data)
    
    def clean_queue_routines(self):
        self.queue_routines = [ 
            routine for routine in self.queue_routines
            if routine.running
        ]
            
    def run_routine(self, routine_data):
        type_routine = routine_data['type_routine']
        if type_routine == 'fme':
            routine_selected = RoutinesFme(self.iface)
        else:
            routine_selected = RoutinesLocal(self.iface)
        routine_selected.sap_mode = self.sap_mode
        routine_selected.run(routine_data)
        self.clean_queue_routines()
        self.queue_routines.append(routine_selected)

        
    
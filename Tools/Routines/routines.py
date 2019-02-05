# -*- coding: utf-8 -*-
from PyQt5 import QtCore
from .routinesFrame import RoutinesFrame
from .routinesLocal import RoutinesLocal
from .routinesFme import RoutinesFme
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import network, msgBox

class Routines(QtCore.QObject):

    def __init__(self, iface):
        super(Routines, self).__init__()
        self.iface = iface
        self.server = False 
        self.sap_mode = False
        self.routine_selected = False
        
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
        self.routinesLocal = RoutinesLocal(self.iface)
        self.routinesLocal.sap_mode = self.sap_mode
        self.routinesLocal.message.connect(
            self.frame.show_message
        )
        self.routinesFme = RoutinesFme(self.iface)
        self.routinesFme.sap_mode = self.sap_mode
        self.routinesFme.message.connect(
            self.frame.show_message
        )
        routines_data = {
            'local' : self.routinesLocal.get_routines_data(),
            'fme' :  self.routinesFme.get_routines_data(server)
        }
        self.frame.load(routines_data)
    
   
    def run_routine(self, routine_data):
        type_routine = routine_data['type_routine']
        if type_routine == 'fme':
            routine_selected = self.routinesFme
        else:
            routine_selected = self.routinesLocal
        routine_selected.run(routine_data)

        
    
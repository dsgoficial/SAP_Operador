# -*- coding: utf-8 -*-
from PyQt5 import QtCore
import sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from SAP.managerSAP import ManagerSAP
from utils import managerQgis, network, msgBox

class Works(QtCore.QObject):

    def __init__(self, iface):
        super(Works, self).__init__()
        self.iface = iface
        self.sap_mode = False
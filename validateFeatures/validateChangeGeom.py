# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui, utils

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))

class ValidateChangeGeom(QtCore.QObject):

    def __init__(self, iface, dataLogin=False):
        super(ValidateChangeGeom, self).__init__()

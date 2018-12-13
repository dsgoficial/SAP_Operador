# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))

class Reshape(QtCore.QObject):

    def __init__(self, iface, parent=None):
        super(Reshape, self).__init__(parent)
        self.iface = iface

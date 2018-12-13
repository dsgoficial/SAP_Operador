# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))

class Monitor_Preview(QtCore.QObject)::

    def __init__(self):
        super(Monitor_Preview, self).__init__()
# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from qgis import core, gui, utils
import sys, os, resources


class ActionTest(QtGui.QAction):
    def __init__(self, iface):
        pathIcon = ":/plugins/Ferramentas_Producao/icons/buttonIcon.png"
        super(ActionTest, self).__init__(
            QtGui.QIcon(pathIcon), 
            u"Ferramentas de Produção", 
            iface.mainWindow()
        )
        self.iface = iface

    def api_backdoor(self):
        print  'hop'
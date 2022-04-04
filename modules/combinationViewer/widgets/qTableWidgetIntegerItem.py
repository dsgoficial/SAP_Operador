import os, sys, copy, json
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

class QTableWidgetIntegerItem(QtWidgets.QTableWidgetItem):

    def __lt__(self, other):
        return int(self.text()) < int(other.text())


# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from qgis import core, gui
from utils import msgBox
from utils.managerQgis import ManagerQgis

class MessageSave(QtCore.QObject):

    def __init__(self, iface, seconds):
        super(MessageSave, self).__init__()
        self.msg = msgBox
        self.is_running = False
        self.iface = iface
        self.seconds = seconds
        self.is_visible = False
        self.half = False
        self.time = QtCore.QTimer()
        btns = [
            self.iface.actionSaveAllEdits(),
            self.iface.actionSaveActiveLayerEdits()
        ]
        for b in btns:
            b.triggered.connect(self.reset_time)

    def reset_time(self):
        self.time.stop()
        self.time.start(self.seconds)
        self.half = False
        
    def show_message(self):
        m_qgis = ManagerQgis(self.iface)
        if m_qgis.count_modified_layer() > 0 and not(self.is_visible) and self.half:
            html = u'<p style="color:red">Salve suas alterações!</p>'
            self.is_visible = True
            msgBox.show(text=html, title=u"Aviso")
            self.is_visible = False
        else:
            self.half = True
            
    def start(self):
        self.time.timeout.connect(self.show_message)
        self.time.start(self.seconds)
        self.is_running = True
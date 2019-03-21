# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
from qgis import core, gui
from utils.timer import Timer
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

    def show_message(self):
        m_qgis = ManagerQgis(self.iface)
        if m_qgis.count_modified_layer() > 0 and not(self.is_visible):
            html = u'<p style="color:red">Salve suas alterações!</p>'
            self.is_visible = True
            msgBox.show(text=html, title=u"Aviso")
            self.is_visible = False
            

    def start(self):
        self.worker = Timer(self.seconds)
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.worker.alarm.connect(
            self.show_message
        )
        self.thread.started.connect(
            self.worker.run
        )
        self.thread.start()
        self.is_running = True

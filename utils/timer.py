# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets
import json, requests, os
from time import sleep

RUNNING = 1


class Timer(QtCore.QObject):

    alarm = QtCore.pyqtSignal()

    def __init__(self, seconds):
        super(Timer, self).__init__()
        self.seconds = seconds

    def run(self):
        while RUNNING:
            sleep(self.seconds)
            self.alarm.emit()

# -*- coding: utf-8 -*-
from PyQt5 import QtCore, uic, QtWidgets
import os, sys, platform, pickle


def dump_data(path_data, data):
    with open(path_data, u"wb") as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

def load_data(path_data):
    try:
        with open(path_data, u"rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return False
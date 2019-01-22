# -*- coding: utf-8 -*-
from PyQt5 import QtCore 
from qgis import gui, core
import base64

def save_project_var(key, value):
    chiper_text = base64.b64encode(value.encode('ascii'))
    core.QgsExpressionContextUtils.setProjectVariable(
        core.QgsProject().instance(), 
        key,
        chiper_text.decode('utf-8')
    )

def load_project_var(key):
    current_project  = core.QgsProject().instance()
    chiper_text = core.QgsExpressionContextUtils.projectScope(current_project).variable(
        key
    )
    value = base64.b64decode(str.encode(chiper_text)).decode('utf-8') if chiper_text else ''
    return value

def save_qsettings_var(key, value):
    qsettings = QtCore.QSettings()
    qsettings.setValue(key, value)

def load_qsettings_var(key):
    qsettings = QtCore.QSettings()
    return qsettings.value(key)
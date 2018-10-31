# -*- coding: utf-8 -*-
from qgis import gui, core
from qgis.core import QgsProject
from PyQt4.QtCore import QSettings, Qt
from PyQt4.QtGui import QToolBar, QPushButton
import sys, os
sys.path.append(os.path.dirname(__file__))

class ProjectQgis:

    def __init__(self, iface):
        self.iface = iface
        self.qsettings = QSettings()

    def setProjectVariable(self, varName, value):
        core.QgsExpressionContextUtils.setProjectVariable(
            varName, value
        )

    def getVariableProject(self, varName, isJson=False):
        data = core.QgsExpressionContextUtils.projectScope().variable(
            varName
        )
        if isJson and not(data) and varName == 'loginData':
            return 'e30='
        elif isJson and not(data):
            return '{}'
        return data

    def getVariableLayer(self, varname):
        layer = self.iface.activeLayer()
        data = core.QgsExpressionContextUtils().layerScope(layer).variable(
            varname
        )
        return data

    def configShortcut(self):
        #s.setValue("Qgis/newProjectDefault", u'true')
        self.cleanShortcut()
        variables = self.getVariables()
        for variable in variables:
            self.qsettings.setValue(variable, variables[variable])
        
    def cleanShortcut(self):
        for variableQgis in self.qsettings.allKeys():
            if (u'shortcuts' in variableQgis):
                self.qsettings.setValue(variableQgis, u'')

    def delFeature(self):
        self.iface.activeLayer().deleteSelectedFeatures()

    def qsettings_insert(self, key, value):
        self.qsettings.setValue(key, value)
    
    def qsettings_select(self, key):
        return self.qsettings.value(key)

    def getVariables(self):
        'Definicao de todas as configuracoes em portugues e ingles'
        variables = {
            u'shortcuts/Sair do QGIS' : u'',
            u'shortcuts/Exit QGIS' : u'',
            u'shortcuts/Mesclar fei\xe7\xf5es selecionadas' : u'M',
            u'shortcuts/Merge Selected Features' : u'M',
            u'shortcuts/Quebrar Fei\xe7\xf5es' : u'C',
            u'shortcuts/Split Features' : u'C',
            u'shortcuts/Identificar fei\xe7\xf5es': u'I',
            u'shortcuts/Identify Features': u'I',
            u'shortcuts/Adicionar fei\xe7\xe3o': u'A',
            u'shortcuts/Add Feature': u'A',
            u'shortcuts/Desfazer sele\xe7\xe3o de fei\xe7\xf5es em todas as camadas': u'D',
            u'shortcuts/Deselect Features from All Layers': u'D',
            u'shortcuts/Ferramenta de n\xf3s' : u'N',
            u'shortcuts/Node Tool' : u'N',
            u'shortcuts/Salvar para todas as camadas' : u'Ctrl+S',
            u'shortcuts/Save for All Layers' : u'Ctrl+S',
            u'shortcuts/Habilitar tra\xe7ar' : u'T',
            u'shortcuts/Enable Tracing' : u'T',
            u'shortcuts/Remodelar fei\xe7\xf5es' : u'R',
            u'shortcuts/Reshape Features' : u'R',
            u'shortcuts/\xc1rea' : u'Z',
            u'shortcuts/Measure Area' : u'Z',
            u'shortcuts/Linha' : u'X',
            u'shortcuts/Measure Line' : u'X',
            u'shortcuts/DSGTools: Generic Selector': u'S',
            u'shortcuts/DSGTools: Seletor Gen\xe9rico': u'S',
            u'shortcuts/DSGTools: Right Degree Angle Digitizing': u'E',
            u'shortcuts/DSGTools: Ferramenta de aquisi\xe7\xe3o com \xe2ngulos retos': u'E',
            u'Qgis/parallel_rendering' : u'true',
            u'Qgis/max_threads' : 8,
            u'Qgis/simplifyDrawingHints': u'0',
            u'cache/size': 1048576,
            u'Qgis/digitizing/marker_only_for_selected' : u'true',
            u'Qgis/digitizing/default_snap_mode' : u'to vertex and segment',
            u'Qgis/default_selection_color_alpha': u'127',
            u'shortcuts/Salvar' : u'',
            u'shortcuts/Save' : u'',
            u'shortcuts/Select Feature(s)' : u'V',
            u'shortcuts/Fei\xe7\xe3o(s)' : u'V',
            u'shortcuts/DSGTools: Inspecionar anterior': u'Q',
            u'shortcuts/DSGTools: Back Inspect': u'Q',
            u'shortcuts/DSGTools: Inspecionar pr\xf3ximo': u'W',
            u'shortcuts/DSGTools: Next Inspect': u'W',
            u'shortcuts/DSGTools: Desenhar Forma': u'G',
            u'shortcuts/DSGTools: Draw Shape': u'G',
            u'shortcuts/Desfazer' : u'',
            u'shortcuts/Undo' : u'',
            u'shortcuts/Undo' : u'',
            u'shortcuts/Mostrar camadas selecionadas' : u'U',
            u'shortcuts/Show Selected Layers' : u'U',
            u'shortcuts/Esconder camadas selecionadas' : u'Y',
            u'shortcuts/Hide Selected Layers' : u'Y'
                          }
        return variables


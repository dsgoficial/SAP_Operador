# -*- coding: utf-8 -*-
from PyQt5 import QtCore 
from qgis import gui, core
import base64

class ManagerQgis(QtCore.QObject):

    def __init__(self, iface):
        super(ManagerQgis, self).__init__()
        self.iface = iface

    def save_project_var(self, key, value):
        chiper_text = base64.b64encode(value.encode('utf-8'))
        core.QgsExpressionContextUtils.setProjectVariable(
            core.QgsProject().instance(), 
            key,
            chiper_text.decode('utf-8')
        )

    def load_project_var(self, key):
        current_project  = core.QgsProject().instance()
        chiper_text = core.QgsExpressionContextUtils.projectScope(current_project).variable(
            key
        )
        value = base64.b64decode(str.encode(chiper_text)).decode('utf-8') if chiper_text else ''
        return value

    def save_qsettings_var(self, key, value):
        qsettings = QtCore.QSettings()
        qsettings.setValue(key, value)

    def load_qsettings_var(self, key):
        qsettings = QtCore.QSettings()
        return qsettings.value(key)

    def load_custom_config(self):
        self.clean_custom_config()
        configs = self.get_custom_config()
        qsettings = QtCore.QSettings()
        for var_qgis in configs:
            qsettings.setValue(var_qgis, configs[var_qgis])
        
    def clean_custom_config(self):
        qsettings = QtCore.QSettings()
        for var_qgis in qsettings.allKeys():
            if (u'shortcuts' in var_qgis):
                qsettings.setValue(var_qgis, u'')

    def get_custom_config(self):
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
            u'shortcuts/Ferramenta Vértice (Camada Atual)' : u'N',
            u'shortcuts/Vertex Tool (Current Layer)' : u'N',
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
            u'shortcuts/Hide Selected Layers' : u'Y',
            u'shortcuts/Toggle Snapping' : u''
        }
        return variables


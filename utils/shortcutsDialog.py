# -*- coding: utf-8 -*-
import os
from PyQt5 import QtWidgets, uic

class ShortcutsDialog(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'shortcutsDialog.ui'
    )

    def __init__(self):
        super(ShortcutsDialog, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.load()

    def tag_tamplate(self, description, shortcutkey):
        return '''<p>{0} : {1}</p>'''.format(description, shortcutkey)

    def load(self):
        html = ''
        shortcuts_info = {
            'Mesclar feições selecionadas' : 'M',
            'Quebrar Feições' : 'C',
            'Identificar feições': 'I',
            'Adicionar feições': 'A',
            'Desfazer seleção em todas as camadas': 'D',
            'Ferramenta Vértice (Todas as Camadas)' : 'N',
            'Salvar para todas as camadas' : 'Ctrl+S',
            'Habilitar traçar' : 'T',
            'Remodelar feições' : 'R',
            'Medir área' : 'Z',
            'Medir linha' : 'X',
            'Seletor Genérico': 'S',
            'Ferramenta de aquisição com ângulos retos': 'E',
            'Edição topológica' : 'H',
            'Selecionar feições' : 'V',
            'Inspecionar anterior': 'Q',
            'Inspecionar próximo': 'W',
            'Desenhar Forma': 'G',
            'Liga/Desliga todas as labels' : 'L',
            'Ferramenta de Aquisição à Mão Livre' : 'F',
            'Remodelar feições mão livre' : 'Shift+R'
        }
        for descr in shortcuts_info:
            html += self.tag_tamplate(descr, shortcuts_info[descr])
        self.textEdit.setHtml(html)
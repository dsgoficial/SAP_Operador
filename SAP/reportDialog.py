# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import network, msgBox

class ReportDialog(QtWidgets.QDialog):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'reportDialog.ui'
    )


    def __init__(self, report_config, parent):
        super(ReportDialog, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.parent = parent
        self.report_config = report_config
        self.type_bug_id = {}
        self.buttonBox.accepted.connect(
            self.report
        )
        self.load()

    def load(self):
        if 'dados' in self.report_config:
            self.type_bug_id = {
                d['tipo_problema'] : d['tipo_problema_id']
                for d in self.report_config['dados'] 
            }
            options = sorted(list(self.type_bug_id.keys()))
            self.type_cb.addItems(options)
            
    def report(self):
        type_bug_name = self.type_cb.currentText()
        report_input = {
            "tipo_problema_id" : self.type_bug_id[type_bug_name] ,
            "descricao" : self.descr_text.toPlainText() 
        }
        result = self.show_message('report')
        if result == 16384:
            self.parent.report_bug.emit(report_input)

    def show_message(self, tag):
        dialog = self
        if "report" == tag:
            html = u"<p>Reportando um problema sua atividade atual será finalizada.</p>"
            result = msgBox.show(
                text=html, 
                title=u"AVISO!", 
                status="question", 
                parent=dialog
            )
            return result
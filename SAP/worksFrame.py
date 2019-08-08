# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
from .worksItem import WorksItem
from .worksCloseDialog import WorksCloseDialog
from .reportDialog import ReportDialog
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
from utils import msgBox, cursorWait
from utils.managerQgis import ManagerQgis
from datetime import datetime

class WorksFrame(QtWidgets.QFrame):

    dialog_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 
        'worksFrame.ui'
    )

    close_works = QtCore.pyqtSignal()
    report_bug = QtCore.pyqtSignal(dict)

    def __init__(self, iface, parent):
        super(WorksFrame, self).__init__()
        uic.loadUi(self.dialog_path, self)
        self.spacer_item = None
        self.iface = iface
        self.parent = parent
        self.sap_data = {}
        self.load()

    def clean_works(self):
        layout = self.activity_area.layout()
        for idx in range(layout.count()):
            if type(layout.itemAt(idx)) == QtWidgets.QtWidgetItem:
                layout.itemAt(idx).widget().deleteLater()
        layout.removeItem(self.spacer_item) if self.spacer_item else ''

    def text_to_timestamp(self, text):
        year, month, day = text.split('T')[0].split('-')
        h, m, s = text.split('T')[1].split('.')[0].split(':')
        date = datetime(int(year), int(month), int(day), int(h), int(m), int(s))
        return date

    def load(self):
        self.clean_works()
        self.sap_data = self.parent.load_data()
        self.works_item = WorksItem(self.sap_data, self)
        self.works_item.enable_btn.connect(lambda:self.close_works_btn.setEnabled(True))
        self.works_item.disable_btn.connect(lambda:self.close_works_btn.setEnabled(False))
        self.activity_area.layout().addWidget(self.works_item)
        self.spacer_item = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.activity_area.layout().addItem(self.spacer_item)
        lineage = {}
        for d in self.sap_data['dados']['atividade']['linhagem']:
            date_end = self.text_to_timestamp(d['data_fim'])
            date_begin = self.text_to_timestamp(d['data_inicio'])
            d['date_end'] = date_end
            d['date_begin'] = date_begin
            lineage[date_end] = d
        for i, k in enumerate(sorted(list(lineage.keys()))):
            text = "Etapa : {0}\nData inicio : {1}\nData fim : {2}\nNome : {3} {4}".format(
                lineage[k]['etapa'], 
                lineage[k]['date_begin'].strftime('%H:%M %d-%m-%Y') ,
                lineage[k]['date_end'].strftime('%H:%M %d-%m-%Y'), 
                lineage[k]['posto_grad'], 
                lineage[k]['nome_guerra']
            )
            lb = QtWidgets.QLabel(text)
            lb.setStyleSheet('QLabel { background-color: white }')
            self.lineage_area.layout().addWidget(lb)
        self.spacer_item2 = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.lineage_area.layout().addItem(self.spacer_item2)

    @QtCore.pyqtSlot(bool)
    def on_close_works_btn_clicked(self, b):
        user_name = self.sap_data['user']
        m_qgis = ManagerQgis(self.iface)
        if m_qgis.count_modified_layer() > 0:
            html = u'<p style="color:red">Salve todas suas alterações antes de finalizar!</p>'
            msgBox.show(text=html, title=u"Aviso", parent=self)
        else:
            worksCloseDialog  = WorksCloseDialog(self.iface, user_name)
            worksCloseDialog.finish.connect(
                self.close_works.emit
            )
            worksCloseDialog.exec_()

    @QtCore.pyqtSlot(bool)
    def on_report_btn_clicked(self, b):
        cursorWait.start()
        try:
            report_config = self.parent.get_report_data()
            diag = ReportDialog(report_config, self)
        finally:
            cursorWait.stop()
        diag.exec_()

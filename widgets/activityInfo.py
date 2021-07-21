from Ferramentas_Producao.widgets.widget import Widget
from Ferramentas_Producao.interfaces.IActivityInfoWidget import IActivityInfoWidget

from PyQt5 import QtWidgets, QtGui, QtCore

class ActivityInfo(Widget, IActivityInfoWidget):

    def __init__(self, controller=None):
        super(ActivityInfo, self).__init__(controller)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.endActivityButton = QtWidgets.QPushButton('Finalizar', self)
        self.endActivityButton.setEnabled(False)
        self.endActivityButton.clicked.connect(
            lambda: self.getController().showEndActivityDialog()
        )

    def setEPSG(self, title, description):
        self.layout.addWidget(
            QtWidgets.QLabel(
                "<b>{0}</b> {1}".format(title, description), 
                self
            )
        )
        
    def setDescription(self, title, description):
        self.layout.addWidget(
            QtWidgets.QLabel(
                "<b>{0}</b><br>{1}".format(title, description), 
                self
            )
        )
    
    def setNotes(self, title, notes):            
        self.layout.addWidget(QtWidgets.QLabel("<b>{0}</b>".format(title), self))
        for note in notes:
            self.layout.addWidget(QtWidgets.QLabel(note, self))
    
    def setRequirements(self, title, requirements):
        self.layout.addWidget( QtWidgets.QLabel("<b>{0}</b>".format(title), self) )
        if not requirements:
            self.endActivityButton.setEnabled(True)
        for item in requirements:
            cbx = QtWidgets.QCheckBox(item['descricao'], self)
            cbx.stateChanged.connect( self.updateEndActivityButton )
            self.layout.addWidget(cbx)

    def setButtons(self):
        layout = QtWidgets.QHBoxLayout()
        layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                150, 
                20,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding
            )
        )
        layout.addWidget(self.endActivityButton)
        self.reportErrorButton = QtWidgets.QPushButton('Reportar problema', self)
        self.reportErrorButton.clicked.connect(
            lambda: self.getController().showReportErrorDialog()
        )
        layout.addWidget(self.reportErrorButton)
        self.layout.addLayout(layout)

    def updateEndActivityButton(self):
        if self.allRequirementsChecked():
            self.endActivityButton.setEnabled(True)
        else:
            self.endActivityButton.setEnabled(False)

    def allRequirementsChecked(self):
        for idx in range(self.layout.count()):
            widget = self.layout.itemAt(idx).widget()
            if not( type(widget) == QtWidgets.QCheckBox ):
                continue
            if not widget.isChecked():
                return False
        return True
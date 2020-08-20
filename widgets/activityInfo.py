from Ferramentas_Producao.widgets.widget import Widget
from Ferramentas_Producao.interfaces.IActivityInfoWidget import IActivityInfoWidget

from PyQt5 import QtWidgets, QtGui, QtCore

class ActivityInfo(Widget, IActivityInfoWidget):

    def __init__(self, mediator=None):
        super(ActivityInfo, self).__init__(mediator)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        
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
        for item in requirements:
            cbx = QtWidgets.QCheckBox(item['descricao'], self)
            cbx.stateChanged.connect( self.updateEndActivityButton )
            self.layout.addWidget(cbx)

    def setButtons(self):
        layout = QtWidgets.QHBoxLayout()
        self.endActivityButton = QtWidgets.QPushButton('Finalizar', self)
        self.endActivityButton.setEnabled(False)
        self.endActivityButton.clicked.connect(
            lambda: self.getMediator().notify(self, 'endActivity')
        )
        layout.addWidget(self.endActivityButton)
        self.reportErrorButton = QtWidgets.QPushButton('Reportar problema', self)
        self.reportErrorButton.clicked.connect(
            lambda: self.getMediator().notify(self, 'errorActivity')
        )
        layout.addWidget(self.reportErrorButton)
        layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                150, 
                20,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding
            )
        )
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
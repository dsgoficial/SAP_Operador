from SAP_Operador.widgets.widget import Widget
from SAP_Operador.interfaces.IActivityInfoWidget import IActivityInfoWidget
from SAP_Operador.modules.qgis.qgisApi import QgisApi
import json
from PyQt5 import QtWidgets, QtGui, QtCore
import textwrap

wrapper = textwrap.TextWrapper(width=40)

class ActivityInfo(Widget, IActivityInfoWidget):

    def __init__(self, controller=None):
        super(ActivityInfo, self).__init__(controller)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.endActivityButton = QtWidgets.QPushButton('Finalizar', self)
        self.endActivityButton.setEnabled(False)
        self.endActivityButton.clicked.connect(self.finish)
        self.reportErrorButton = QtWidgets.QPushButton('Reportar problema', self)
        self.reportErrorButton.clicked.connect(self.reportError)
        self.qgis = QgisApi()

    def finish(self, b):
        self.endActivityButton.setEnabled(False)
        self.getController().showEndActivityDialog()
        self.endActivityButton.setEnabled(True)

    def reportError(self):
        try:
            self.getController().showReportErrorDialog()
        except Exception as e:
            self.showErrorMessageBox('Aviso', str(e))

    def hideButtons(self, hide):
        visible = not hide
        self.endActivityButton.setVisible(visible)
        self.reportErrorButton.setVisible(visible)

    def addObservation(self, title, description):
        self.layout.addWidget(
            QtWidgets.QLabel(
                "<b>{0}</b> <span>{1}</span>".format(title, '<br/>'.join(
                    wrapper.wrap(text=description)
                )), 
                self
            )
        )
        
    def setDescription(self, title, description):
        self.layout.addWidget(
            QtWidgets.QLabel(
                '<span style="font-size: 15px;"><span>{0}</span></span>'.format(
                    '<br/>'.join(wrapper.wrap(text=description)
                )), 
                self
            )
        )
    
    def setNotes(self, title, notes):            
        self.layout.addWidget(QtWidgets.QLabel("<b>{0}</b>".format(title), self))
        for note in notes:
            self.layout.addWidget(QtWidgets.QLabel('<span>{0}</span>'.format('<br/>'.join(wrapper.wrap(text=note))), self))
    
    def setRequirements(self, title, requirements):
        if not requirements:
            self.endActivityButton.setEnabled(True)
            return
        self.layout.addWidget( QtWidgets.QLabel("<b>{0}</b>".format(title), self) )
        for item in requirements:
            description = item['descricao']
            cbx = QtWidgets.QCheckBox('\n'.join(wrapper.wrap(text=description)), self)
            savedState = self.getRequirementState(description)
            cbx.setCheckState(savedState)
            self.updateEndActivityButton(savedState, description)
            cbx.stateChanged.connect( lambda state, description=description: self.updateEndActivityButton(state, description) )
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
        layout.addWidget(self.reportErrorButton)
        self.layout.addLayout(layout)

    

    def updateEndActivityButton(self, state, description):
        self.setRequirementState(description, state)
        if self.allRequirementsChecked():
            self.endActivityButton.setEnabled(True)
        else:
            self.endActivityButton.setEnabled(False)

    def setRequirementState(self, description, state):
        activityName = self.qgis.getProjectVariable('productiontools:activityName')
        checklist = self.qgis.getSettingsVariable('productiontools:checklist')
        if not checklist:
            self.qgis.setSettingsVariable(
                'productiontools:checklist', 
                json.dumps(
                    {
                        activityName: {
                            description: state
                        }
                    }
                )
            )
            return
        checklist = json.loads(checklist)
        if not( activityName in checklist):
            self.qgis.setSettingsVariable(
                'productiontools:checklist', 
                json.dumps(
                    {
                        activityName: {
                            description: state
                        }
                    }
                )
            )
            return
        checklist[activityName][description] = state
        self.qgis.setSettingsVariable(
            'productiontools:checklist', 
            json.dumps(checklist)
        )

    def getRequirementState(self, description):
        activityName = self.qgis.getProjectVariable('productiontools:activityName')
        checklist = self.qgis.getSettingsVariable('productiontools:checklist')
        if not checklist:
            return QtCore.Qt.CheckState.Unchecked
        checklist = json.loads(checklist)
        state = int(checklist[activityName][description]) if activityName in checklist and description in checklist[activityName] else QtCore.Qt.CheckState.Unchecked
        return state

    def allRequirementsChecked(self):
        for idx in range(self.layout.count()):
            widget = self.layout.itemAt(idx).widget()
            if not( type(widget) == QtWidgets.QCheckBox ):
                continue
            if not widget.isChecked():
                return False
        return True
from SAP_Operador.widgets.widget import Widget

from PyQt5 import QtWidgets, QtGui, QtCore, uic
import os, json

class ActivityRoutines(Widget):

    def __init__(self, controller=None):
        super(ActivityRoutines, self).__init__(controller)
        uic.loadUi(self.getUiPath(), self)
        self.routines = []

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'activityRoutines.ui'
        )

    def addWidget(self, widget):
        self.scrollAreaContents.layout().addWidget(widget)

    def setRoutines(self, routines):
        if not routines:
            return
        for item in routines:
            rb = QtWidgets.QRadioButton(item['description'], self)
            rb.customData = json.dumps(item)
            self.addWidget(rb)
        self.routines = routines

    def hasData(self):
        return self.routines != []

    def getRoutineSelected(self):
        for idx in range(self.scrollAreaContents.layout().count()):
            item = self.scrollAreaContents.layout().itemAt(idx)
            widget = item.widget()
            if widget is None or not widget.isChecked():
                continue
            return json.loads(widget.customData)

    def adjustWidgets(self):
        self.scrollAreaContents.layout().addSpacerItem(
            QtWidgets.QSpacerItem(
                20, 
                150,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding
            )
        )

    @QtCore.pyqtSlot(bool)
    def on_runRoutineBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.getController().runRoutine(self.getRoutineSelected())
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
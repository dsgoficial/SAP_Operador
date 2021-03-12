from Ferramentas_Producao.widgets.widget import Widget

from PyQt5 import QtWidgets, QtGui, QtCore, uic
import os, json

class ActivityInputs(Widget):

    def __init__(self, controller=None):
        super(ActivityInputs, self).__init__(controller)
        uic.loadUi(self.getUiPath(), self)

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'activityInputs.ui'
        )

    def addWidget(self, widget):
        self.scrollAreaContents.layout().addWidget(widget)

    def setInputs(self, inputData):
        if not inputData:
            return
        for item in inputData:
            cbx = QtWidgets.QCheckBox(item['nome'], self)
            cbx.customData = json.dumps(item)
            self.addWidget(cbx)

    def getInputsSelected(self):
        inputData = []
        for idx in range(self.scrollAreaContents.layout().count()):
            item = self.scrollAreaContents.layout().itemAt(idx)
            widget = item.widget()
            if widget is None or not widget.isChecked():
                continue
            inputData.append(json.loads(widget.customData))
        return inputData

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
    def on_loadInputsBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            results = self.getController().loadActivityInputs(self.getInputsSelected())
            self.showErrorMessageBox( 'Download Insumos', ''.join( results ) ) if results else ''
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
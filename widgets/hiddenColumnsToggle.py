from SAP_Operador.widgets.widget import Widget

from qgis.PyQt import QtWidgets, QtCore

class HiddenColumnsToggle(Widget):

    def __init__(self, controller=None):
        super(HiddenColumnsToggle, self).__init__(controller)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.showHiddenCkb = QtWidgets.QCheckBox('Exibir colunas ocultas', self)
        self.showHiddenCkb.setToolTip(
            'Reexibe, na tabela de atributos e no formulário, as colunas que o projeto '
            'oculta por padrão nesta atividade. Desmarque para voltar a ocultá-las.'
        )
        self.showHiddenCkb.setChecked(self.getController().areHiddenColumnsVisible())
        self.showHiddenCkb.toggled.connect(self.handleToggled)
        layout.addWidget(self.showHiddenCkb)

    def hasData(self):
        return self.getController().hasHiddenColumns()

    @QtCore.pyqtSlot(bool)
    def handleToggled(self, checked):
        self.getController().setHiddenColumnsVisible(checked)

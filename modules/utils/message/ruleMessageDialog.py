
import os
from PyQt5 import QtWidgets, uic, QtCore
from Ferramentas_Producao.modules.utils.interfaces.IMessage  import IMessage
from .errorMessageBox import ErrorMessageBox

class RuleMessageDialog(QtWidgets.QDialog, IMessage):

    def __init__(self):
        super(RuleMessageDialog, self).__init__()
        uic.loadUi(self.getUIPath(), self)
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(['Nome', 'Resultado'])
        self.errorMessage = ErrorMessageBox()
        
    def getUIPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'ruleMessageDialog.ui'
        )

    def showErrorMessageBox(self, title, text):
        self.errorMessage.show(self, title, text)

    def show(self, parent, title, result, qgis):
        if result is None:
            self.showErrorMessageBox(
                title,
                "<p style=\"color:red\">{0}</p>".format(
                    'Não há regras para as camadas carregadas!'
                )
            )
            return
        self.setWindowTitle(title)
        for rule in result:
            parentItem = QtWidgets.QTreeWidgetItem(self.treeWidget)
            self.treeWidget.setItemWidget(
                parentItem,
                0, 
                QtWidgets.QLabel(
                    '<h3>{0}</h3>'.format(rule)
                )
            )
            if not(result[rule]):
                childItem   = QtWidgets.QTreeWidgetItem(self.treeWidget)
                self.treeWidget.setItemWidget(
                    childItem,
                    1, 
                    QtWidgets.QLabel(
                        "<p style=\"color:green\">{0}</p>".format(
                            "As camadas passaram em todas as regras."
                        )
                    )
                )
                parentItem.addChild(childItem)
                continue
            color = self.getRuleColor(rule)
            for layerName in result[rule]:
                childItem   = QtWidgets.QTreeWidgetItem(self.treeWidget)
                layerButton = QtWidgets.QPushButton(layerName)
                layerButton.clicked.connect(lambda b, name=layerName: qgis.setActiveLayerByName(name))
                layerButton.setStyleSheet('QPushButton { color: '+color+';}')
                self.treeWidget.setItemWidget(
                    childItem,
                    1, 
                    layerButton
                )
                parentItem.addChild(childItem)
        self.treeWidget.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        super().show()


    def getRuleColor(self, rule):
        colors = {
            'Atributo incomum': 'yellow',
            'Atributo incorreto': 'red',
            'Preencher Atributo': 'orange'
        }
        return 'red' if not(rule in colors) else colors[rule]
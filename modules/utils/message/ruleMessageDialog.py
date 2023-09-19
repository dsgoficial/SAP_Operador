
import os
from PyQt5 import QtWidgets, uic, QtCore
from Ferramentas_Producao.modules.utils.interfaces.IMessage  import IMessage
from .errorMessageBox import ErrorMessageBox
from qgis.utils import iface

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
            color = self.getRuleColor(rule.split(':')[1].strip())
            for layerName in result[rule]:
                childItem   = QtWidgets.QTreeWidgetItem(self.treeWidget)
                layerButton = QtWidgets.QPushButton(layerName)
                font = layerButton.font()
                font.setPointSize(13)
                layerButton.setFont(font)
                layerButton.clicked.connect(lambda b, name=layerName, qgis=qgis: self.handleLayerButton(qgis, name))
                layerButton.setStyleSheet('QPushButton { color: '+color+'; background-color: #000000;}')
                self.treeWidget.setItemWidget(
                    childItem,
                    1, 
                    layerButton
                )
                parentItem.addChild(childItem)
        self.treeWidget.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        super().show()

    def handleLayerButton(self, qgis, name):
        qgis.setActiveLayerByName(name)
        iface.actionOpenTable().trigger()

    def getRuleColor(self, rule):
        colors = {
            'Atributo incomum': 'yellow',
            'Atributo incorreto': 'red',
            'Preencher atributo': 'orange'
        }
        return 'red' if not(rule in colors) else colors[rule]
import os, sys, copy, json
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from SAP_Operador.modules.utils.factories.utilsFactory import UtilsFactory
from .tableFunctions import TableFunctions

class CombinationViewerDlg(QtWidgets.QDialog, TableFunctions):

    def __init__(self, 
            controller=None, 
            parent=None,
            messageFactory=None
        ):
        super(CombinationViewerDlg, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.controller = controller
        self.messageFactory = UtilsFactory().createMessageFactory() if messageFactory is None else messageFactory
        self.setup()

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'combinationViewerDlg.ui'
        )

    def getController(self):
        return self.controller

    def setup(self):
        self.layerSelection.setup({
            'title': 'Camadas',
            'send': {
                'columns': ['Nome']
            },
            'selection': {
                'columns': ['Nome']
            }
        })
        self.layerSelection.selectionChange.connect(self.loadCommonFields)
        self.fieldSelection.setup({
            'title': 'Campos Comuns',
            'send': {
                'columns': ['Nome']

            },
            'selection': {
                'columns': ['Nome']
            }
        })
        self.fieldSelection.selectionChange.connect(self.loadCommonAttributes)
        self.attributeSelection.setup({
            'title': 'Atributos Comuns',
            'send': {
                'columns': ['Valor', 'Quantidade', 'dump']
            },
            'selection': {
                'columns': ['Valor', 'Quantidade', 'dump']
            }
        })
        self.attributeSelection.selectionChange.connect(self.loadLayersFound)
        self.attributeSelection.setSendColumnHidden(2, True)
        self.attributeSelection.setSelectionColumnHidden(2, True)
        self.layersFoundTw.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.adjustColumns(self.layersFoundTw)
        self.adjustRows(self.layersFoundTw)

    def loadLayerNames(self, names):
        self.layerSelection.addSendRows([ [n] for n in names ])

    def getSelectedLayerNames(self):
        return [
            row[0]
            for row in self.layerSelection.getSelectedData()
        ]

    def loadCommonFields(self):
        self.fieldSelection.clearSendRows()
        self.fieldSelection.clearSelectionRows()
        selectedLayerNames = self.getSelectedLayerNames()
        if not selectedLayerNames:
            return
        self.fieldSelection.addSendRows(
            self.getController().filterCommonFields(
                selectedLayerNames
            )
        )

    def getSelectedFields(self):
        return [
            row[0]
            for row in self.fieldSelection.getSelectedData()
        ]

    def loadCommonAttributes(self):
        self.attributeSelection.clearSendRows()
        self.attributeSelection.clearSelectionRows()
        selectedLayerNames = self.getSelectedLayerNames()
        if not selectedLayerNames:
            return
        selectedFields = self.getSelectedFields()
        if not selectedFields:
            return
        self.attributeSelection.addSendRows(
            self.getController().filterAttributeCombination(
                selectedFields,
                selectedLayerNames
            )
        )

    def loadLayersFound(self):
        self.clearAllItems(self.layersFoundTw)
        selectedLayerNames = self.getSelectedLayerNames()
        if not selectedLayerNames:
            return
        selectedAttributes = self.getSelectedAttributes()
        if not selectedAttributes:
            return selectedAttributes
        self.addRows(
            self.layersFoundTw, 
            self.getController().getLayersByAttributes(selectedAttributes, selectedLayerNames)
        )  

    def getSelectedAttributes(self):
        fields = [
            json.loads(row[2])
            for row in self.attributeSelection.getSelectedData()
        ]
        return fields

    

            

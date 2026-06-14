from SAP_Operador.widgets.widget import Widget
from SAP_Operador.widgets.editionMetadataDialog import EditionMetadataDialog

import os
import json
from qgis.PyQt import QtWidgets, QtCore


class EditionMetadata(Widget):
    """Secao do dock so visivel em atividade da fase de Edicao (tipo_fase_id = 4).

    Dois botoes: editar o metadado por folha (nome do produto e palavras-chave,
    gravado no SAP na hora) e baixar o JSON de edicao de cada folha (rota publica
    do SAP por uuid do produto)."""

    def __init__(self, controller=None, sap=None):
        super(EditionMetadata, self).__init__(controller)
        self.sap = sap
        self.setupUi()

    def setSap(self, sap):
        self.sap = sap

    def getSap(self):
        return self.sap

    def setupUi(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.editBtn = QtWidgets.QPushButton('Editar metadados', self)
        self.editBtn.clicked.connect(self.onEditClicked)
        self.downloadBtn = QtWidgets.QPushButton('Baixar JSON', self)
        self.downloadBtn.clicked.connect(self.onDownloadClicked)
        layout.addWidget(self.editBtn)
        layout.addWidget(self.downloadBtn)

    def hasData(self):
        if not self.sap:
            return False
        try:
            return self.sap.getActivityDataModel().getPhaseTypeId() == 4
        except Exception:
            return False

    def onEditClicked(self, checked=False):
        dataModel = self.sap.getActivityDataModel()
        produtos = dataModel.getEditionMetadata()
        if not produtos:
            self.showInfoMessageBox(
                'Aviso', 'Nenhum produto (folha) associado a esta atividade de edição.'
            )
            return
        keywordTypes = self.sap.getKeywordTypes()
        dlg = EditionMetadataDialog(produtos, keywordTypes, self)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        metadados = dlg.getMetadados()
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            message = self.sap.saveEditionMetadata(metadados)
            dataModel.setEditionMetadata(self._mergeSaved(produtos, metadados))
        except Exception as e:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.showErrorMessageBox('Erro', 'Erro ao salvar metadados:\n{0}'.format(str(e)))
            return
        QtWidgets.QApplication.restoreOverrideCursor()
        self.showInfoMessageBox('Sucesso', message)

    def _mergeSaved(self, produtos, metadados):
        byId = {m['produto_id']: m for m in metadados}
        merged = []
        for p in produtos:
            novo = dict(p)
            saved = byId.get(p['produto_id'])
            if saved:
                novo['nome_produto'] = saved['nome_produto']
                novo['palavras_chave'] = saved['palavras_chave']
            merged.append(novo)
        return merged

    def onDownloadClicked(self, checked=False):
        dataModel = self.sap.getActivityDataModel()
        produtos = dataModel.getEditionMetadata()
        if not produtos:
            self.showInfoMessageBox(
                'Aviso', 'Nenhum produto (folha) associado a esta atividade de edição.'
            )
            return
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Pasta para salvar os JSON de edição'
        )
        if not folder:
            return
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        resultados = []
        try:
            for p in produtos:
                uuid = p.get('produto_uuid')
                label = self._produtoLabel(p)
                if not uuid:
                    resultados.append('{0}: sem uuid, ignorado'.format(label))
                    continue
                try:
                    dados = self.sap.getEditionJson(uuid)
                except Exception as e:
                    resultados.append('{0}: erro - {1}'.format(label, str(e)))
                    continue
                jsonObj = dados.get('json') if dados else None
                erros = dados.get('erros') if dados else None
                if not jsonObj:
                    resultados.append('{0}: JSON não gerado'.format(label))
                    continue
                fileName = '{0}.json'.format(self._produtoFileName(p))
                filePath = os.path.join(folder, fileName)
                with open(filePath, 'w', encoding='utf-8') as f:
                    json.dump(jsonObj, f, ensure_ascii=False, indent=2)
                if erros:
                    resultados.append('{0}: salvo COM avisos - {1}'.format(fileName, '; '.join(erros)))
                else:
                    resultados.append('{0}: salvo'.format(fileName))
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        self.showInfoMessageBox('Baixar JSON', '\n'.join(resultados))

    def _produtoLabel(self, p):
        return p.get('mi') or p.get('inom') or p.get('nome_produto') or str(p.get('produto_id'))

    def _produtoFileName(self, p):
        name = p.get('mi') or p.get('inom') or p.get('nome_produto') or str(p.get('produto_id'))
        return name.replace(' ', '_').replace('/', '_')

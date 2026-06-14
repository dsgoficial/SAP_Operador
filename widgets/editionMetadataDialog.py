from qgis.PyQt import QtWidgets, QtCore


class EditionMetadataDialog(QtWidgets.QDialog):
    """Edita, por folha, o nome do produto e as palavras-chave (nome + tipo).

    Recebe a lista de produtos da atividade (cada um com produto_id, mi, inom,
    nome_produto e palavras_chave) e a lista de tipos de palavra-chave do SAP.
    Mantem as edicoes de todas as folhas em memoria; Salvar devolve todas, e
    Cancelar descarta tudo.
    """

    def __init__(self, produtos, keywordTypes, parent=None):
        super(EditionMetadataDialog, self).__init__(parent)
        self.produtos = produtos
        self.keywordTypes = keywordTypes if keywordTypes else []
        self.state = {}
        for p in produtos:
            self.state[p['produto_id']] = {
                'nome_produto': p.get('nome_produto') or '',
                'palavras_chave': [dict(k) for k in (p.get('palavras_chave') or [])],
            }
        self.currentProdutoId = None
        self.setupUi()
        if produtos:
            self.onProdutoChanged(0)

    def setupUi(self):
        self.setWindowTitle('Editar metadados de edição')
        self.resize(540, 480)
        layout = QtWidgets.QVBoxLayout(self)

        formLayout = QtWidgets.QFormLayout()
        self.produtoCombo = QtWidgets.QComboBox(self)
        for p in self.produtos:
            self.produtoCombo.addItem(self._produtoLabel(p), p['produto_id'])
        self.produtoCombo.currentIndexChanged.connect(self.onProdutoChanged)
        formLayout.addRow('Folha:', self.produtoCombo)

        self.nomeEdit = QtWidgets.QLineEdit(self)
        formLayout.addRow('Nome do produto:', self.nomeEdit)
        layout.addLayout(formLayout)

        layout.addWidget(QtWidgets.QLabel('Palavras-chave:', self))
        self.kwTable = QtWidgets.QTableWidget(0, 2, self)
        self.kwTable.setHorizontalHeaderLabels(['Palavra-chave', 'Tipo'])
        self.kwTable.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.kwTable.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.kwTable)

        btnLayout = QtWidgets.QHBoxLayout()
        self.addBtn = QtWidgets.QPushButton('Adicionar', self)
        self.addBtn.clicked.connect(lambda: self.addKeywordRow())
        self.removeBtn = QtWidgets.QPushButton('Remover', self)
        self.removeBtn.clicked.connect(self.removeSelectedRow)
        btnLayout.addWidget(self.addBtn)
        btnLayout.addWidget(self.removeBtn)
        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            QtCore.Qt.Orientation.Horizontal,
            self,
        )
        self.buttonBox.accepted.connect(self.onAccept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def _produtoLabel(self, p):
        return p.get('mi') or p.get('inom') or p.get('nome_produto') or str(p.get('produto_id'))

    def _typeCode(self, t):
        return t.get('code', t.get('id'))

    def _typeName(self, t):
        return t.get('nome', t.get('descricao', ''))

    def _makeTypeCombo(self, selectedCode=None):
        combo = QtWidgets.QComboBox()
        defaultIndex = 0
        for i, t in enumerate(self.keywordTypes):
            combo.addItem(self._typeName(t), self._typeCode(t))
            if selectedCode is not None and self._typeCode(t) == selectedCode:
                defaultIndex = i
            elif selectedCode is None and 'topon' in self._typeName(t).lower():
                defaultIndex = i
        combo.setCurrentIndex(defaultIndex)
        return combo

    def addKeywordRow(self, nome='', tipoCode=None):
        row = self.kwTable.rowCount()
        self.kwTable.insertRow(row)
        self.kwTable.setItem(row, 0, QtWidgets.QTableWidgetItem(nome or ''))
        self.kwTable.setCellWidget(row, 1, self._makeTypeCombo(tipoCode))

    def removeSelectedRow(self, checked=False):
        row = self.kwTable.currentRow()
        if row >= 0:
            self.kwTable.removeRow(row)

    def _readTable(self):
        palavras = []
        for row in range(self.kwTable.rowCount()):
            item = self.kwTable.item(row, 0)
            nome = item.text().strip() if item else ''
            combo = self.kwTable.cellWidget(row, 1)
            tipoCode = combo.currentData() if combo else None
            if not nome or tipoCode is None:
                continue
            palavras.append({'nome': nome, 'tipo_palavra_chave_id': tipoCode})
        return palavras

    def _flushCurrent(self):
        if self.currentProdutoId is None:
            return
        self.state[self.currentProdutoId]['nome_produto'] = self.nomeEdit.text().strip()
        self.state[self.currentProdutoId]['palavras_chave'] = self._readTable()

    def onProdutoChanged(self, index):
        self._flushCurrent()
        produtoId = self.produtoCombo.itemData(index)
        self.currentProdutoId = produtoId
        st = self.state.get(produtoId, {'nome_produto': '', 'palavras_chave': []})
        self.nomeEdit.setText(st['nome_produto'])
        self.kwTable.setRowCount(0)
        for k in st['palavras_chave']:
            self.addKeywordRow(k.get('nome'), k.get('tipo_palavra_chave_id'))

    def onAccept(self):
        self._flushCurrent()
        for p in self.produtos:
            st = self.state[p['produto_id']]
            if not st['nome_produto']:
                QtWidgets.QMessageBox.warning(
                    self, 'Atenção', 'Informe o nome do produto para todas as folhas.'
                )
                idx = self.produtoCombo.findData(p['produto_id'])
                if idx >= 0:
                    self.produtoCombo.setCurrentIndex(idx)
                return
        self.accept()

    def getMetadados(self):
        return [
            {
                'produto_id': pid,
                'nome_produto': st['nome_produto'],
                'palavras_chave': st['palavras_chave'],
            }
            for pid, st in self.state.items()
        ]

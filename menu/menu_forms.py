#! -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui


class Menu_forms(QtGui.QDialog):
    
    ok = QtCore.pyqtSignal(dict, dict)

    def __init__(self):
        super(Menu_forms, self).__init__()
        self.resize(500, 600)
        self.verticalLayout_2 = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(self)
        self.verticalLayout_2.addWidget(self.label)
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 378, 439))
        self.verticalLayout = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.scrollArea)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.okButton = QtGui.QPushButton(self)
        self.okButton.setText("Confirmar")
        self.okButton.clicked.connect(self.confirm)
        self.horizontalLayout.addWidget(self.okButton)
        self.cancelButton = QtGui.QPushButton(self)
        self.cancelButton.setText("Cancelar")
        self.cancelButton.clicked.connect(self.cancel)
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.fields = {}
        self.formValues = {}
        self.dbJson = None
        self.tabWidgetMenu = None
        self.layout = QtGui.QVBoxLayout(self)
                
    def cancel(self):
        self.deleteLater()

    def confirm(self):
        self.ok.emit(
            self.formValues, 
            self.fields
        )

    def clearLayout(self):
        layout = self.layout
        for i in reversed(range(layout.count())):
            item = layout.takeAt(i)
            for x in reversed(range(item.count())):
                    i = item.takeAt(x)
                    i.widget().close()
                    item.removeItem(i)
            layout.removeItem(item) 

    def addPushButton(self, data):
        horizontalLayout = QtGui.QHBoxLayout()
        label = QtGui.QLabel(self.scrollAreaWidgetContents)
        label.setText(data['label'])
        horizontalLayout.addWidget(label)
        pushButton = QtGui.QPushButton(self.scrollAreaWidgetContents)
        pushButton.setText(data['text'])
        pushButton.setObjectName(data['label'])
        self.formValues[data['label']] = u''
        horizontalLayout.addWidget(pushButton)
        self.verticalLayout.addLayout(horizontalLayout)
        return pushButton

    def addLineEdit(self, data):
        horizontalLayout = QtGui.QHBoxLayout()
        label = QtGui.QLabel(self.scrollAreaWidgetContents)
        label.setText(data['label'])
        horizontalLayout.addWidget(label)
        lineEdit = QtGui.QLineEdit(self.scrollAreaWidgetContents)
        lineEdit.setText(data['valueDefault'])
        lineEdit.setObjectName(data['label'])
        if not('no_connect' in data):
            lineEdit.textEdited.connect(lambda:self.insertLineEditValue(lineEdit))
            self.formValues[data['label']] = u''
        horizontalLayout.addWidget(lineEdit)
        if data['valueDefault']:
            self.formValues[data['label']] = data['valueDefault']
        if 'layout' in data:
            data['layout'].addLayout(horizontalLayout)
        else:
            self.verticalLayout.addLayout(horizontalLayout)
        return lineEdit

    def addComboBox(self, data):
        horizontalLayout = QtGui.QHBoxLayout()
        label = QtGui.QLabel(self.scrollAreaWidgetContents)
        label.setText(data['label'])
        horizontalLayout.addWidget(label)
        comboBox = QtGui.QComboBox(self.scrollAreaWidgetContents)
        comboBox.addItems(sorted(data['items']))
        comboBox.setObjectName(data['label'])
        comboBox.setMaximumWidth(500)
        if not('no_connect' in data):
            comboBox.currentIndexChanged.connect(
                lambda:self.insertComboBoxValue(comboBox)
            )
            self.formValues[data['label']] = comboBox.currentText()
        horizontalLayout.addWidget(comboBox)
        if 'valueDefault' in data:
            index = comboBox.findText( 
                data['valueDefault'], QtCore.Qt.MatchFixedString
            )  
        else: 
            index = comboBox.findText(
                "A SER PREENCHIDO", QtCore.Qt.MatchFixedString
            )
        if index >= 0:
            comboBox.setCurrentIndex(index)
        if 'layout' in data:
            data['layout'].addLayout(horizontalLayout)
        else:
            self.verticalLayout.addLayout(horizontalLayout)
        return comboBox 

    def addCheckBox(self, checkBoxLabel, checkBoxName):
        horizontalLayout = QtGui.QHBoxLayout()
        checkBox = QtGui.QCheckBox(
            checkBoxLabel, 
            self.scrollAreaWidgetContents
        )
        checkBox.setObjectName(checkBoxName)
        checkBox.stateChanged.connect(
            lambda:self.insertCheckBoxValue(checkBox)
        )
        horizontalLayout.addWidget(checkBox)
        self.verticalLayout.addLayout(horizontalLayout)
        return checkBox

    def insertLineEditValue(self, le):
        self.formValues[le.objectName()] = le.text().strip()

    def insertComboBoxValue(self, cb):
        self.formValues[cb.objectName()] = cb.currentText().strip()

    def insertCheckBoxValue(self, cb):
        self.formValues[cb.objectName()] = cb.isChecked()

    def createAddTabForm(self):
        self.label.setText(u'Adicionar Aba :')
        line = self.addLineEdit({
                'label' : u'Nome da aba:',
                'valueDefault' :  u'',
        })
        
    def createDelTabForm(self, items):
        self.label.setText(u'Remover Aba :')
        combo = self.addComboBox({
                'label' : u'Selecione Aba para remover:',
                'items' : [x for x in items if x not in [u'**Pesquisa**', u'**Opções**']],
        })
        return combo

    def createAddButtonForm(self, dbname, dbJson, tabsNames):
        self.label.setText(u'Adicionar Botão:')
        self.addLineEdit({
            'label' : u'*Nome do botão:',
            'valueDefault' :  u'',
        }) 
        self.addComboBox({
            'label' : u'*Selecione aba:',
            'items' : [x for x in tabsNames if x not in [u'**Pesquisa**', u'**Opções**']],
        })
        cbLayer = self.addComboBox({
            'label' : u'*Selecione camada:',
            'items' : [u'<opções>']+sorted(dbJson['listOfLayers']),
        })
        self.addComboBox({
            'label' : u'Fechar form na aquisição:',
            'items' : [u'Sim', u'Não']
        })
        self.addComboBox({
            'label' : u'Escolha ferramenta de aquisição:',
            'items' : [u'Normal', u'Mão livre', u'Angulor reto', u'Circulo'],
            'valueDefault' : u'Normal',
        })
        self.addLineEdit({
            'label' : u'Definir palavras chaves(separar com ";"):',
            'valueDefault' :  u'',
        }) 
        cbLayer.currentIndexChanged.connect(
            lambda:self.loadFieldsOfLayer(cbLayer)
        )
        self.verticalLayout.addLayout(
            self.layout
        )
        self.dbJson = dbJson
        self.dbname = dbname

    def loadFieldsOfLayer(self, cbLayer):
        self.clearLayout()
        groups = {
            'a' : 'AREA', 
            'c' : 'PONTO',
            'p' : 'PONTO', 
            'd' : 'LINHA',
            'l' : 'LINHA',
        }
        layerName = cbLayer.currentText()
        groupGeom = groups[layerName.split('_')[-1]]
        groupLayer = layerName.split('_')[0]
        fields = self.dbJson[self.dbname]\
            [groupGeom][groupLayer][layerName]
        for field in fields:
            if not(field in ['loadFormUi', 
                             'data_modificacao', 
                             'controle_id', 
                             'ultimo_usuario', 
                             'id']): 
                if fields[field] and (u'ValueMap' in fields[field]):
                    self.addComboBox({
                        'label' : field,
                        'items' : fields[field]['ValueMap'].keys(),
                        'layout' : self.layout,
                        'valueDefault' :  u'IGNORAR',
                    })
                elif not fields[field]:
                    self.addLineEdit({
                        'label' : field,
                        'valueDefault' :  u'',
                        'layout' : self.layout,
                    })
        self.fields = fields

    def createDelButtonForm(self, tabWidgetMenu):
        self.label.setText(u'Remover Botão:')
        tabCombo = self.addComboBox({
                'label' : '*Selecionar aba:',
                'items' : [u'<Opções>']+[x for x in tabWidgetMenu.getAllNamesTabs().keys() if x not in [u'**Pesquisa**', u'**Opções**']]
            })
        buttonLayerCombo = self.addComboBox({
                'label' : u'*Selecionar botão:',
                'items' : [],
            })
        tabCombo.currentIndexChanged.connect(
            lambda:self.loadLayerComboDelForm(
                tabCombo,
                buttonLayerCombo,
                tabWidgetMenu,
            )
        )

    def loadLayerComboDelForm(self, tabCombo, bLyrCombo, tWgMenu):
        bLyrCombo.clear()
        if tabCombo.currentIndex() > 0:
            tabName = tabCombo.currentText()
            buttons = tWgMenu.getAllButtonLayerOnTabByName(tabName)
            bLyrCombo.addItems(buttons.keys())

    def createLoadProfileFromFileForm(self):
        self.label.setText(u'Carregar Perfil do Menu de Arquivo:')
        pushButton = self.addPushButton({
            'label' : u'*Selecion o arquivo com o perfil:',
            'text' :  u'...'
        })
        pushButton.clicked.connect(
            lambda:self.getPathFile(pushButton)
        )

    def getPathFile(self, bt):
        file_ext = "JSON (*.json);;"
        filePath = QtGui.QFileDialog.getOpenFileName(self, "Carregar Perfil", "", file_ext)
        if filePath:
            bt.setText(filePath)
            self.formValues[bt.objectName()] = filePath

    def createSaveProfileOnFileForm(self, profiles, profileSelected):
        self.label.setText(u'Salvar Perfil do Menu no Arquivo:')
        self.addComboBox({
            'label' : u'Selecione o perfil do menu:',
            'items' : profiles,
            'valueDefault' :  profileSelected,
        })
        self.addLineEdit({
            'label' : u'*Informe o nome do Arquivo:',
            'valueDefault' :  u'',
        }) 
        pushButton = self.addPushButton({
            'label' : u'*Selecion uma pasta para salvar o arquivo:',
            'text' :  u'...'
        })
        pushButton.clicked.connect(
            lambda:self.getPathDiretory(pushButton)
        )
        

    def getPathDiretory(self, bt):
        pathDest = unicode(QtGui.QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino:")).encode('utf-8') 
        if pathDest:
            bt.setText(pathDest)
            self.formValues[bt.objectName()] = pathDest

    def createSaveProfileOnDbForm(self):
        self.label.setText(u'Salvar Perfil do Menu no Banco de Dados:')
        self.addLineEdit({
            'label' : u'*Informe o nome do perfil:',
            'valueDefault' :  u'',
        }) 
        
    def createEditTabForm(self, tabWidgetMenu):
        fields = tabWidgetMenu.getAllNamesTabs()
        self.label.setText(u'Editar Aba :')
        self.addComboBox({
            'label' : u'*Selecione a aba:',
            'items' : [u'<opções>']+[x for x in fields.keys() if x not in [u'**Pesquisa**', u'**Opções**']],
            'valueDefault' :  u'<opções>',
        })
        line = self.addLineEdit({
                'label' : u'*Novo nome para aba:',
                'valueDefault' :  u'',
        }) 
        self.fields = fields

    def createEditButtonForm(self, tabWidgetMenu):
        tabs = tabWidgetMenu.getAllNamesTabs()
        self.label.setText(u'Editar Botão:')
        cbTabs = self.addComboBox({
            'label' : u'*Selecione aba:',
            'items' : [u'<opções>']+[x for x in tabs.keys() if x not in [u'**Pesquisa**', u'**Opções**']],
        })
        cbButtons = self.addComboBox({
            'label' : u'*Selecione botão:',
            'items' : [u'<opções>'],
        })
        self.verticalLayout.addLayout(
            self.layout
        )
        cbTabs.currentIndexChanged.connect(
            lambda:self.updateButtonsComboEditButtonForm(cbTabs, cbButtons, tabWidgetMenu)
        )
        cbButtons.currentIndexChanged.connect(
            lambda:self.loadFieldsToEditButton(cbTabs, cbButtons, tabWidgetMenu)
        )

    def updateButtonsComboEditButtonForm(self, cbTabs, cbButtons, tabWidgetMenu):
        tabName = cbTabs.currentText()
        if tabName != u'<opções>':
            allButtonsOnTab = tabWidgetMenu.getAllButtonLayerOnTabByName(
                tabName
            )
            cbButtons.clear()
            cbButtons.addItems([u'<opções>']+allButtonsOnTab.keys())
        else:
            cbButtons.clear()
            self.clearLayout()
            cbButtons.addItems([u'<opções>'])

    def loadFieldsToEditButton(self, cbTabs, cbButtons, tabWidgetMenu):
        self.clearLayout()
        buttonName = cbButtons.currentText()
        tabName = cbTabs.currentText()
        if buttonName and buttonName != u'<opções>' and tabName !=  u'<opções>':            
            allButtonsOnTab = tabWidgetMenu.getAllButtonLayerOnTabByName(
                tabName
            )
            button = allButtonsOnTab[buttonName]
            formValuesBefore = button.buttonData['formValues']
            fieldsBefore = button.buttonData['fields']
            self.addLineEdit({
                    'label' : u'Nome botão : ',
                    'layout' : self.layout,
                    'valueDefault' : button.objectName(),
            })
            for field in formValuesBefore:
                if field == u'Escolha ferramenta de aquisição:':
                    self.addComboBox({
                        'label' : u'Escolha ferramenta de aquisição:',
                        'items' : [u'Normal', u'Mão livre', u'Angulo reto', u'Circulo'],
                        'valueDefault' :  formValuesBefore[field],
                        'layout' : self.layout,
                    })
                elif field == u'Definir palavras chaves(separar com ";"):':
                    self.addLineEdit({
                        'label' : u'Definir palavras chaves(separar com ";"):',
                        'valueDefault' :  formValuesBefore[field],
                        'layout' : self.layout,
                    })                 
                elif field == u'Fechar form na aquisição:':
                    self.addComboBox({
                        'label' : u'Fechar form na aquisição:',
                        'items' : [u'Sim', u'Não'],
                        'valueDefault' :  formValuesBefore[field],
                        'layout' : self.layout,
                    })                
            for field in fieldsBefore:
                if not(field in ['loadFormUi', 
                                'data_modificacao', 
                                'controle_id', 
                                'ultimo_usuario', 
                                'id']):
                    if fieldsBefore[field] and (u'ValueMap' in fieldsBefore[field]):
                        self.addComboBox({
                            'label' : field,
                            'items' : fieldsBefore[field]['ValueMap'].keys()+["IGNORAR"],
                            'layout' : self.layout,
                            'valueDefault' : formValuesBefore[field],
                        })
                    elif not fieldsBefore[field]:
                        self.addLineEdit({
                            'label' : field,
                            'valueDefault' :  u'',
                            'layout' : self.layout,
                            'valueDefault' : formValuesBefore[field],
                        })
            self.fields = {'buttonOld' : button}
          
    def createEditButtonShortcutForm(self, button):
        self.setWindowTitle(u'Formulário')
        self.label.setText(u'Editar Botão:')
        #self.okButton.setVisible(False)
        fields =  button.buttonData['fields']
        formValuesBefore = button.buttonData['formValues']
        self.verticalLayout.addLayout(
            self.layout
        )
        self.addLineEdit({
                    'label' : u'Nome botão : ',
                    'layout' : self.layout,
                    'valueDefault' : button.objectName(),
        })
        for field in formValuesBefore:
            if field == u'Escolha ferramenta de aquisição:':
                self.addComboBox({
                    'label' : u'Escolha ferramenta de aquisição:',
                    'items' : [u'Normal', u'Mão livre', u'Angulor reto', u'Circulo'],
                    'valueDefault' :  formValuesBefore[field],
                    'layout' : self.layout,
                })
            elif field == u'Definir palavras chaves(separar com ";"):':
                self.addLineEdit({
                    'label' : u'Definir palavras chaves(separar com ";"):',
                    'valueDefault' :  formValuesBefore[field],
                    'layout' : self.layout,
                })                 
            elif field == u'Fechar form na aquisição:':
                self.addComboBox({
                    'label' : u'Fechar form na aquisição:',
                    'items' : [u'Sim', u'Não'],
                    'valueDefault' :  formValuesBefore[field],
                    'layout' : self.layout,
                })                
        for field in fields:
            if not(field in ['loadFormUi', 
                             'data_modificacao', 
                             'controle_id', 
                             'ultimo_usuario', 
                             'id']):
                if fields[field] and (u'ValueMap' in fields[field]):
                    self.addComboBox({
                        'label' : field,
                        'items' : fields[field]['ValueMap'].keys()+["IGNORAR"],
                        'layout' : self.layout,
                        'valueDefault' : formValuesBefore[field],
                    })
                elif not fields[field]:
                    self.addLineEdit({
                        'label' : field,
                        'valueDefault' :  u'',
                        'layout' : self.layout,
                        'valueDefault' : formValuesBefore[field],
                    })
        self.fields = fields
        #self.scrollAreaWidgetContents.setEnabled(False)
                 
    def createFormConfirmReclassification(self, button, lyrsSelected):
        self.resize(700, 600)
        self.setWindowTitle(u'Formulário')
        self.label.setText(u'Confirme a reclassificação:')
        self.fields = lyrsSelected
        fields =  button.buttonData['fields']
        formValuesBefore = button.buttonData['formValues']
        for name in lyrsSelected:
            checkBox = self.addCheckBox(
                u'Camada : {0} >>> Quantidade de selecionados : {1}'.format(
                    name, len(lyrsSelected[name])
                ),
                u'{0}_cbx'.format(name)
            )
            checkBox.setChecked(True)
        self.verticalLayout.addItem(
            QtGui.QSpacerItem(20, 48, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        )
        self.verticalLayout.addLayout(
            self.layout
        )
        for field in fields:
            if not(field in ['loadFormUi', 
                             'data_modificacao', 
                             'controle_id', 
                             'ultimo_usuario', 
                             'id']):
                if fields[field] and (u'ValueMap' in fields[field]):
                    self.addComboBox({
                        'label' : field,
                        'items' : fields[field]['ValueMap'].keys()+["IGNORAR"],
                        'layout' : self.layout,
                        'valueDefault' : formValuesBefore[field],
                    })
                elif not fields[field]:
                    self.addLineEdit({
                        'label' : field,
                        'valueDefault' :  u'',
                        'layout' : self.layout,
                        'valueDefault' : formValuesBefore[field],
                    })


    
        
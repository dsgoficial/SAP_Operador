#! -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

class Menu_button(QtGui.QToolButton):

    run =  QtCore.pyqtSignal(object)
    editedButtonData = QtCore.pyqtSignal(str, object)
    openForm = QtCore.pyqtSignal(object)
    
    def __init__(self, data):
        super(Menu_button, self).__init__(data[u'parent'])
        self.buttonData = data[u'buttonData']
        self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
        self.clicked.connect(
            self.startButton
        )
        self.styleDefault = ''
        menu = QtGui.QMenu(self)
        self.setMenu(menu)
        self.action = QtGui.QAction(u'Exibir atributos do botão', menu)
        self.action.triggered.connect(
            self.openFormButton
        )
        menu.addAction(self.action)

    def startButton(self):
        self.run.emit(self)

    def openFormButton(self):
        self.openForm.emit(self)

    def createButtonLayer(self):
        self.setHorizontalSizeExpandig()
        nameButton = self.buttonData['formValues'][u'*Nome do botão:']
        layerName = self.buttonData['formValues'][u'*Selecione camada:']
        self.setText(nameButton)
        self.setObjectName(nameButton)
        styles = {
            'a' : "color: rgb(255, 255, 255); \
                  background-color: rgb(246, 13, 13);", 
            'c' : "background-color: rgb(85, 255, 0);",
            'p' : "color: rgb(255, 255, 255); \
                  background-color: rgb(0, 0, 255);", 
            'd' : "background-color: rgb(255, 255, 0);",
            'l' : "background-color: rgb(21, 7, 7); \
                  color: rgb(255, 255, 255);",
        }
        self.styleDefault = styles[layerName.split('_')[-1]]
        self.setStyleSheet(self.styleDefault)
                        
    def setHorizontalSizeExpandig(self): 
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

    def finishEditAttributes(self, formValues, fields):
        buttonData = self.buttonData['formValues']
        oldName = self.objectName()
        newName = formValues[u'Nome bot\xe3o : ']
        buttonData[u'*Nome do bot\xe3o:'] = newName
        formatName = '%s_%s'%(newName, self.text().split('_')[-1])
        short = self.shortcut()
        self.setText(formatName)
        self.setObjectName(newName)
        self.setShortcut(short)
        for field in formValues:
            if field in buttonData:
                buttonData[field] = formValues[field]
        self.editedButtonData.emit(oldName, self)



    
        
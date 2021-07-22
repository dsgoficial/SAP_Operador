# -*- coding: utf-8 -*-
import os, sys
from PyQt5 import QtCore, uic, QtWidgets
from Ferramentas_Producao.config import Config
from Ferramentas_Producao.modules.sap.interfaces.ILogin  import ILogin
from Ferramentas_Producao.modules.utils.factories.utilsFactory import UtilsFactory

class Login(QtWidgets.QDialog, ILogin):

    def __init__(
            self, 
            controller,
            messageFactory=UtilsFactory().createMessageFactory()
        ):
        super(Login, self).__init__()
        uic.loadUi(self.getLoginDialogUiPath(), self)
        self.setWindowTitle(Config.NAME)
        self.version_text.setText("<b>versão: {}</b>".format(Config.VERSION))
        self.controller = controller
        self.messageFactory = messageFactory
        self.currentFrame = None

    def setController(self, controller):
        self.controller = controller

    def getController(self):
        return self.controller

    def showErrorMessageBox(self, title, message):
        errorMessageBox = self.messageFactory.createMessage('ErrorMessageBox')
        errorMessageBox.show(self, title, message)

    def getLoginDialogUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'login.ui'
        )

    def getRemoteLoginFrameUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'remoteLoginFrame.ui'
        )

    def getLocalLoginFrameUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'localLoginFrame.ui'
        )

    def loadLoginFrame(self, frameType):
        frameTypes = {
            0: self.loadRemoteLoginFrame(),
            1: self.loadLocalLoginFrame()
        }
        frame = frameTypes[frameType]
        self.cleanLoginFrame()
        self.setCurrentLoginFrame(frame)
        self.loginFrameWidget.layout().addWidget(frame)

    def loadLocalLoginFrame(self):
        frame = uic.loadUi(self.getLocalLoginFrameUiPath())
        for dbsetting in self.getController().getQgisDatabaseSettings():
            frame.databasesCb.addItem(dbsetting['alias'], dbsetting)
        return frame

    def loadRemoteLoginFrame(self):
        frame = uic.loadUi(self.getRemoteLoginFrameUiPath())
        server, user, password = self.getController().getRemoteSettings()
        frame.userLe.setText(user) 
        frame.serverLe.setText(server)  
        frame.passwordLe.setText(password)
        return frame

    def setCurrentLoginFrame(self, frame):
        self.currentFrame = frame

    def getCurrentLoginFrame(self):
        return self.currentFrame

    def cleanLoginFrame(self):
        layout = self.loginFrameWidget.layout()
        if not layout:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is None:
                continue
            widget.deleteLater()

    @QtCore.pyqtSlot(int)
    def on_modeSlider_valueChanged(self, frameType):
        self.loadLoginFrame(frameType)

    def getCurrentLoginMode(self):
        return self.modeSlider.value()

    def isCurrentRemoteMode(self):
        return self.getCurrentLoginMode() == 0

    @QtCore.pyqtSlot(bool)
    def on_submitBtn_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            if self.isCurrentRemoteMode():
                self.loginRemote()
                return
            self.loginLocal()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def loginRemote(self):
        try:
            if not self.isValidRemoteInput():
                html = u'<p style="color:red">Todos os campos devem ser preenchidos!</p>'
                self.showErrorMessageBox('Aviso', html)
                return
            frame = self.getCurrentLoginFrame()
            success = self.getController().remoteAuthUser(
                frame.userLe.text(), 
                frame.passwordLe.text(), 
                frame.serverLe.text()
            )
            if success:
                self.getController().loadRemoteDockWidget()
                self.accept()
            else:
                self.reject()
        except Exception as e:
            self.showErrorMessageBox('Erro', str(e))

    def isValidRemoteInput(self):
        frame = self.getCurrentLoginFrame()
        return ( 
            frame.serverLe.text() 
            and  
            frame.userLe.text() 
            and
            frame.passwordLe.text()
        )

    def loginLocal(self):
        #try:
        frame = self.getCurrentLoginFrame()
        dbsetting = frame.databasesCb.itemData(frame.databasesCb.currentIndex())
        self.getController().localAuthUser(
            dbsetting['username'],
            dbsetting['password'],
            dbsetting['host'],
            dbsetting['port'],
            dbsetting['database']
        )
        self.getController().loadLocalDockWidget()
        self.accept()
        #except Exception as e:
        #    self.showErrorMessageBox('Erro', str(e))
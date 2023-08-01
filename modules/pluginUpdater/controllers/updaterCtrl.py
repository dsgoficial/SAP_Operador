from modules.pluginUpdater.factories.updaterFactory import UpdaterFactory
from modules.pluginUpdater.factories.guiFactory import GuiFactory
from modules.qgis.qgisApi import QgisApi
import json
import os
import subprocess
import platform
import shutil
from PyQt5 import QtCore, uic, QtWidgets

class UpdaterCtrl:
    
    def __init__(self, 
            sap,
            qgis=QgisApi(),
            updaterFactory=UpdaterFactory(),
            guiFactory=GuiFactory(),
            time=QtCore.QTimer()
        ):
        self.sap = sap
        self.qgis = qgis
        self.updaterFactory = updaterFactory
        self.guiFactory = guiFactory
        self.menuBar = None
        self.messageDialog = None
        self.updater = self.getUpdater()
        self.qgis.on('ReadProject', self.checkUpdates)
        self.time = time
        self.time.timeout.connect(self.update)

    def getUpdater(self):
        if platform.system().lower() == 'windows':
            return self.updaterFactory.create('WindowsUpdater', self.qgis)
        if platform.system().lower() == 'linux':
            return self.updaterFactory.create('LinuxUpdater', self.qgis)

    def getUpdaterActions(self):
        iconRootPath = os.path.join(
                os.path.dirname(__file__),
                '..',
                'icons'
        )
        return [
            {
                'name': 'atualizador de plugins local',
                'iconPath': os.path.join(iconRootPath, 'updater.png'),
                'callback': self.openSettingsDialog
            }
        ]
        
    def openSettingsDialog(self):
        pass

    def openMessageDialog(self):
        if self.messageDialog:
            self.messageDialog.close()
        self.messageDialog = self.guiFactory.create('MessageDialog', self)
        self.messageDialog.show()

    def update(self):
        self.updater.update()
        self.qgis.closeQgis()

    def checkUpdates(self):
        remotePluginPath = self.getRemotePluginPath()
        if not remotePluginPath:
            return
        self.updater.setRepositoryPluginsPath(remotePluginPath)
        updates = self.updater.checkUpdates()
        if not updates:
            return
        self.openMessageDialog()
        self.time.start(1000*10)

    def getRemotePluginPath(self):
        res = self.sap.getRemotePluginsPath()
        if 'dados' in res and 'path' in res['dados'] and res['dados']['path']
            return res['dados']['path']
        return None
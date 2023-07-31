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
            qgis=QgisApi(),
            updaterFactory=UpdaterFactory(),
            guiFactory=GuiFactory(),
            time=QtCore.QTimer()
        ):
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
        if not self.validSettings():
            return
        updates = self.updater.checkUpdates()
        if not updates:
            return
        self.openMessageDialog()
        self.time.start(1000*10)

    def validSettings(self):
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'settings.json'), 'r') as f:
            data = json.loads(f.read())
        try:
            if platform.system().lower() == 'windows':
                if (
                data['windows']['repository']
                ):
                    return True
            if platform.system().lower() == 'linux':
                if (
                    data['linux']['repository']
                    and 
                    data['linux']['login']
                    and 
                    data['linux']['password']
                    and 
                    data['linux']['domain']
                ):
                    return True
        except Exception as e:
            print(str(e))
            return False
        return False
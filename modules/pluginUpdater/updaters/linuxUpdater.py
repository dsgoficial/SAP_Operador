import os
import subprocess
import platform
import shutil
import json

class LinuxUpdater:
    
    def __init__(
            self,
            qgis
        ):
        self.qgis = qgis
        self.updates = []

    def update(self):
        for origPath, destPath in self.getUpdates():
            self.downloadFolder(origPath, destPath)

    def setUpdates(self, updates):
        self.updates = updates

    def getUpdates(self):
        return self.updates

    def checkUpdates(self):
        remotePlugins = dict(self.getRemotePlugins())
        localPlugins = dict(self.qgis.getPluginPaths())
        updates = []
        qgisPluginsPath = self.qgis.getQgisPluginsDirPath()
        notDownloaded = list(set(remotePlugins.keys()) - set(localPlugins.keys()))
        for pluginName in notDownloaded:
            updates.append(
                (remotePlugins[pluginName], os.path.join(qgisPluginsPath, pluginName))
            )
        for pluginName, pluginPath in localPlugins.items():
            localHash = self.getLocalFileData(
                os.path.join(
                    pluginPath,
                    'hash.txt'
                )
            )
            if not(pluginName in remotePlugins):
                continue
            remoteHash = self.getRemoteFileData(
                os.path.join(remotePlugins[pluginName], 'hash.txt')
            )
            if localHash == remoteHash:
                continue
            updates.append(
                (remotePlugins[pluginName], os.path.join(qgisPluginsPath, pluginName))
            )
        self.setUpdates(updates)
        return updates

    def getSMBC(self):
        try:
            import smbc
            return smbc
        except:
            pass

    def getRepositoryPluginsPath(self):
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'settings.json'), 'r') as f:
            data = json.loads(f.read())
            repository = data['linux']['repository']
        return repository

    def getRemotePlugins(self):
        repositoryPluginsPath = self.getRepositoryPluginsPath()
        entries = self.getSmbContext().opendir(repositoryPluginsPath).getdents()
        return [
            (entry.name, os.path.join(repositoryPluginsPath, entry.name))

            for entry in entries 
            if 
                entry.smbc_type == self.getSMBC().DIR
                and
                not( entry.name in ['.', '..'])
        ]

    def getLocalFileData(self, filePath):
        try:
            with open(filePath, 'r') as f:
                return f.read().strip().replace('\n', ' ').replace('\r', '')
        except:
            return ''

    def getRemoteFileData(self, filePath):
        source = self.getSmbContext().open(filePath, os.O_RDONLY)
        return source.read().strip().decode("utf-8")

    def downloadFile(self, origPath, destPath):
        source = self.getSmbContext().open(origPath, os.O_RDONLY)
        with open(destPath, 'wb') as f:
            f.write (source.read())

    def downloadFolder(self, origPath, destPath):
        self.deleteFolder(destPath)
        self.createFolder(destPath)
        entries = self.getSmbContext().opendir(origPath).getdents()
        for entry in entries:
            name = entry.name
            if name in ['.', '..']:
                continue
            origEntryPath = os.path.join(origPath, name)
            destEntryPath = os.path.join(destPath, name)
            if entry.smbc_type == self.getSMBC().FILE:
                self.downloadFile(origEntryPath, destEntryPath)
            if entry.smbc_type == self.getSMBC().DIR:
                self.downloadFolder(origEntryPath, destEntryPath)

    def deleteFolder(self, folderPath):
        try:
            shutil.rmtree(folderPath)
        except:
            pass

    def createFolder(self, folderPath):
        try:
            os.mkdir(folderPath)
        except:
            pass

    def getSmbContext(self):
        auth = self.getSmbAuth()
        return self.getSMBC().Context(auth_fn=lambda *args: auth)

    def getSmbAuth(self):
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'settings.json'), 'r') as f:
            data = json.loads(f.read())
            auth = (data['linux']['domain'], data['linux']['login'], data['linux']['password'])
        return auth
import os
import subprocess
import platform
import shutil
import json

class WindowsUpdater:
    
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
            if localHash.strip() == remoteHash.strip():
                continue
            updates.append(
                (remotePlugins[pluginName], os.path.join(qgisPluginsPath, pluginName))
            )
        self.setUpdates(updates)
        return updates

    def getRepositoryPluginsPath(self):
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'settings.json'), 'r') as f:
            data = json.loads(f.read())
            repository = data['windows']['repository']
        return repository

    def getRemotePlugins(self):
        repositoryPluginsPath = self.getRepositoryPluginsPath()
        p = subprocess.Popen(
            'cmd /u /c "dir {0} /B"'.format(repositoryPluginsPath), 
            stdout=subprocess.PIPE, 
            shell=True
        )
        result = p.communicate()
        return [
            (name, os.path.join(repositoryPluginsPath, name))
            for name in result[0].decode('u16').split('\r\n')
        ]

    def getLocalFileData(self, filePath):
        return self.getFileData(filePath)

    def getRemoteFileData(self, filePath):
        return self.getFileData(filePath)

    def getFileData(self, filePath):
        p = subprocess.Popen(
             'cmd /u /c "type {0}"'.format(filePath), 
             stdout=subprocess.PIPE, 
             shell=True
        )
        result = p.communicate()
        return result[0].decode('u16')

    def downloadFolder(self, origPath, destPath):
        self.deleteFolder(destPath)
        self.createFolder(destPath)
        p = subprocess.Popen(
             'cmd /u /c "xcopy {0} {1} /s /e /h /Y"'.format(origPath, destPath), 
             stdout=subprocess.PIPE, 
             shell=True
        )
        result = p.communicate()

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
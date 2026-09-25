import os
import subprocess
import platform
import shutil
import json
from configparser import ConfigParser
from modules.pluginUpdater.updaters.pluginCompatibility import PluginCompatibility

class WindowsUpdater:
    
    def __init__(
            self,
            qgis
        ):
        self.qgis = qgis
        self.updates = []
        self.repository = None

    def update(self):
        for origPath, destPath in self.getUpdates():
            self.downloadFolder(origPath, destPath)

    def setUpdates(self, updates):
        self.updates = updates

    def getUpdates(self):
        return self.updates

    def versiontuple(self, version):
        v = version.strip()
        return tuple(map(int, (v.split("."))))

    def checkUpdates(self):
        remotePlugins = dict(self.getRemotePlugins())
        localPlugins = dict(self.qgis.getPluginPaths())
        updates = []
        qgisPluginsPath = self.qgis.getQgisPluginsDirPath()
        compatibility = PluginCompatibility(self.qgis.getVersion())
        notDownloaded = list(set(remotePlugins.keys()) - set(localPlugins.keys()))
        for pluginName in notDownloaded:
            if not pluginName:
                continue
            if not self.isRemotePluginCompatible(compatibility, pluginName, remotePlugins[pluginName]):
                continue
            updates.append(
                (remotePlugins[pluginName], os.path.join(qgisPluginsPath, pluginName))
            )
        for pluginName, pluginPath in localPlugins.items():
            localVersion = self.getLocalPluginVersion(pluginPath)
            if not(pluginName in remotePlugins):
                continue
            remoteVersion = self.getRemotePluginVersion(remotePlugins[pluginName])
            localVersion = self.versiontuple(localVersion)
            remoteVersion = self.versiontuple(remoteVersion)
            if remoteVersion <= localVersion:
                continue
            if not self.isRemotePluginCompatible(compatibility, pluginName, remotePlugins[pluginName]):
                continue
            updates.append(
                (remotePlugins[pluginName], os.path.join(qgisPluginsPath, pluginName))
            )
        self.setUpdates(updates)
        return updates

    def isRemotePluginCompatible(self, compatibility, pluginName, pluginPath):
        metadataText = ''
        try:
            with open(os.path.join(pluginPath, 'metadata.txt'), encoding='utf-8', errors='replace') as mf:
                metadataText = mf.read()
        except OSError:
            pass
        return compatibility.isCompatible(pluginName, metadataText)

    def setRepositoryPluginsPath(self, repoPath):
        self.repository = repoPath

    def getRepositoryPluginsPath(self):
        return self.repository

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

    def getLocalPluginVersion(self, pluginPath):
        pluginVersion = ''
        try:
            metadataPath = os.path.join(
                pluginPath,
                'metadata.txt'
            )
            with open(metadataPath) as mf:
                cp = ConfigParser()
                cp.read_file(mf)
                pluginVersion = cp.get('general', 'version')
        except:
            pass
        return pluginVersion

    def getRemoteFileData(self, filePath):
        return self.getFileData(filePath)

    def getRemotePluginVersion(self, pluginPath):
        pluginVersion = ''
        try:
            metadataPath = os.path.join(
                pluginPath,
                'metadata.txt'
            )
            with open(metadataPath) as mf:
                cp = ConfigParser()
                cp.read_file(mf)
                pluginVersion = cp.get('general', 'version')
        except:
            pass
        return pluginVersion

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
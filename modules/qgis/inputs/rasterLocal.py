from PyQt5 import QtCore, uic, QtWidgets
import os, platform
from qgis import core, gui, utils
from SAP_Operador.modules.qgis.inputs.inputRaster import InputRaster
from SAP_Operador.modules.qgis.widgets.authSMB import AuthSMB
import copy
import subprocess

class RasterLocal(InputRaster):

    def __init__(self):
        super(RasterLocal, self).__init__()
    
    def load(self, fileData):
        fileDataOutput = self.download(fileData)
        if not fileDataOutput:
            return (False, '<p>"{0}": falha no download do arquivo</p>'.format( fileData['caminho'] ) )
        if not self.loadRaster( fileDataOutput['caminho_arquivo'], fileDataOutput['nome'], fileDataOutput['epsg'] ):
            return (False, '<p>"{0}": falha ao carregar arquivo tente carregar manualmente</p>'.format( fileDataOutput['caminho_arquivo'] ) )
        return (True, '<p>"{0}": arquivo carregado com sucesso</p>'.format( fileDataOutput['caminho_arquivo'] ))

    def getAuthSMB(self):
        authSMB = AuthSMB(utils.iface.mainWindow())
        r = authSMB.exec_()
        if not r:
            return
        return authSMB

    def getPythonVersion(self):
        try:
            import smbc
            return "python3"
        except:
            return "python"

    def getScriptPath(self):
        script_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'scripts',
            'getFileBySMB.py'
        )
        return script_path

    def download(self, fileData):
        fileDataOutput = copy.deepcopy(fileData)
        try:
            downloadFunction = self.getDownloadFunction()
            localFilePath = downloadFunction( fileDataOutput['caminho'], fileDataOutput['caminho_padrao'] )  
            if not( localFilePath and os.path.exists( localFilePath ) ):
                return
            fileDataOutput['caminho_arquivo'] = localFilePath
            return fileDataOutput
        except Exception as e:
            return

    def createDestinationPath(self, pathDest):
        try:
            os.makedirs(pathDest)
        except FileExistsError:
            pass

    def getDownloadFunction(self):
        if platform.system() == 'Windows':
            return self.downloadFileWindows
        return self.downloadFileLinux

    def downloadFileWindows(self, pathOrigin, pathDest):
        pathOrigin = pathOrigin.replace(u"/", u"\\")
        fileName = pathOrigin.split(u"\\")[-1]
        pathDest = pathDest.replace(u"/", u"\\")
        localFilePath = os.path.join(pathDest, fileName)
        command = u'copy "{0}" "{1}"'.format(pathOrigin, pathDest)
        self.createDestinationPath(pathDest)
        self.runSystemCommand(command)
        return localFilePath
    
    def runSystemCommand(self, command):
        proc = os.popen(command)  
        result = proc.read()
        proc.close()

    def downloadFileLinux(self, pathOrigin, pathDest):
        authSMB = self.getAuthSMB()
        if not authSMB:
            return
        pathOrigin = pathOrigin.replace(u"\\", u"/")
        fileName = pathOrigin.split(u"/")[-1] 
        localFilePath = os.path.join(pathDest, fileName)
        command = u'{0} {1} {2} "{3}" {4} {5} {6}'.format(
            self.getPythonVersion(),
            self.getScriptPath(),
            "smb:{0}".format(pathOrigin),
            localFilePath,
            authSMB.user,
            authSMB.passwd,
            authSMB.domain
        )
        self.createDestinationPath(pathDest)
        self.runSystemCommand(command)
        return localFilePath
        
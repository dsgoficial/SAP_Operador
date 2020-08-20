from PyQt5 import QtCore, uic, QtWidgets
import os, platform
from qgis import core, gui, utils
from Ferramentas_Producao.modules.qgis.inputs.inputRaster import InputRaster
from Ferramentas_Producao.modules.qgis.widgets.authSMB import AuthSMB

class RasterLocal(InputRaster):

    def __init__(self):
        super(RasterLocal, self).__init__()
    
    def load(self, fileData):
        result = self.download(fileData)
        if not result:
            self.showErrorMessageBox('Falha ao baixar rasters')
        
        downloadedFiles = result[0]
        unDownloadedFiles = result[1]
        unloadedFiles = []
        
        for d in downloadedFiles:
            if not self.loadRaster(d['caminho_arquivo'], d['nome'], d['epsg']):
                unloadedFiles.append(d)
                continue
        if not(unDownloadedFiles and unloadedFiles):
            return

        self.showErrorMessageBox(''.join(
            [
                '<p>erro: falha no download do arquivo "{0}"</p>'.format(d['caminho']) 
                for d in unDownloadedFiles
            ] +
            [
                '<p>erro: falha ao carregar arquivo "{0}" tente carregar manualmente</p>'.format(d['caminho']) 
                for d in unloadedFiles
            ]
        ))

    def getAuthSMB(self):
        authSMB = AuthSmb(utils.iface.mainWindow())
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
            '..'
            'scripts',
            'getFileBySMB.py'
        )
        return script_path

    def getPathDest(self):
        return QtWidgets.QFileDialog.getExistingDirectory(
            self.parent if self.parent else utils.iface.mainWindow(), 
            u"Selecione pasta de destino dos insumos:",
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )

    def requestFilePath(self, fileData):
        for d in fileData:
            if not d['caminho_padrao']:
                return True
        return False

    def download(self, fileData):
        downloadedFiles = []
        unDownloadedFiles = []
        if self.requestFilePath(fileData):            
            pathDest = self.getPathDest()
            if not pathDest:
                return
        for d in fileData:
            pathOrigin = d['caminho']
            try:
                currentPathDest = d['caminho_padrao'] if d['caminho_padrao'] else pathDest
                downloadFunction = self.getDownloadFunction()
                localFilePath = self.downloadFunction(pathOrigin, currentPathDest)  
                if not(localFilePath and os.path.exists(localFilePath)):
                    unDownloadedFiles.append(d)
                    continue
                d['caminho_arquivo'] = localFilePath
                downloadedFiles.append(d)
            except:
                unDownloadedFiles.append(d)
        return (downloadedFiles, unDownloadedFiles)

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
        proc.read()
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
        
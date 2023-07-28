from Ferramentas_Producao.factories.loginSingleton  import LoginSingleton

class LoginCtrl:
    
    def __init__(self, 
            qgis,
            remoteProdToolsDockCtrl,
            localProdToolsDockCtrl
        ):
        self.qgis = qgis
        self.remoteProdToolsDockCtrl = remoteProdToolsDockCtrl
        self.localProdToolsDockCtrl = localProdToolsDockCtrl
        self.loginView = LoginSingleton.getInstance(controller=self)

    def showView(self):
        self.loginView.exec_()

    def getRemoteSettings(self):
        return (
            self.qgis.getSettingsVariable('productiontools:server'),
            self.qgis.getProjectVariable('productiontools:user'),
            self.qgis.getProjectVariable('productiontools:password')
        )

    def getQgisDatabaseSettings(self):
        return self.qgis.getDatabaseSettings()

    def remoteAuthUser(self, username, password, server):
        self.qgis.setProjectVariable('productiontools:user', username)
        self.qgis.setProjectVariable('productiontools:password', password)
        self.qgis.setSettingsVariable('productiontools:server', server)
        return self.remoteProdToolsDockCtrl.authUser(username, password, server)

    def loadRemoteDockWidget(self):
        self.remoteProdToolsDockCtrl.loadDockWidget()

    def localAuthUser(self, dbusername, dbpassword, dbhost, dbport, dbname):
        return self.localProdToolsDockCtrl.authUser(dbusername, dbpassword, dbhost, dbport, dbname)

    def loadLocalDockWidget(self, dbusername, dbpassword, dbhost, dbport, dbname):
        self.localProdToolsDockCtrl.loadDockWidget(dbusername, dbpassword, dbhost, dbport, dbname)

class ILogin(object):
    
    def setController(self, controller):
        raise NotImplementedError('Abstract Method')

    def getController(self, controller):
        raise NotImplementedError('Abstract Method')

    def loadData(self, user, server):
        raise NotImplementedError('Abstract Method')

    def showView(self):
        raise NotImplementedError('Abstract Method')

    def closeView(self):
        raise NotImplementedError('Abstract Method')

    def showErroMessage(self, title, text):
        raise NotImplementedError('Abstract Method')

    def login(self):
        raise NotImplementedError('Abstract Method')
    
    

    
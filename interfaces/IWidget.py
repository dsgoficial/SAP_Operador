class IWidget:
        
    def setController(self, controller):
        raise NotImplementedError('Abstract Method')

    def getController(self):
        raise NotImplementedError('Abstract Method')

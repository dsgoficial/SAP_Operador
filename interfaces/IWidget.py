class IWidget:
        
    def setController(self, controller):
        raise NotImplementedError('Abstract Method')

    def setMediator(self, mediator):
        raise NotImplementedError('Abstract Method')

    def getMediator(self):
        raise NotImplementedError('Abstract Method')

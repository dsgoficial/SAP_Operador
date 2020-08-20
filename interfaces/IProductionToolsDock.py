

class IProductionToolsDock:

    def addActivityWidget(self, name, widget):
        raise NotImplementedError('Abstract Method')
        
    def showMessageErro(self, title, text):
        raise NotImplementedError('Abstract Method')

    def showMessageInfo(self, title, text):
        raise NotImplementedError('Abstract Method')
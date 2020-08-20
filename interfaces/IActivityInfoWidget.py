
class IActivityInfoWidget(object):

    def onlyWithFeatures(self):
        raise NotImplementedError('Abstract Method')

    def setDescription(self, *args):
        raise NotImplementedError('Abstract Method')
    
    def setNotes(self, *args):            
        raise NotImplementedError('Abstract Method')
    
    def setRequirements(self, *args):
        raise NotImplementedError('Abstract Method')

    def setButtons(self, *args):
        raise NotImplementedError('Abstract Method')
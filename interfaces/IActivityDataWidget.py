
class IActivityDataWidget(object):

    def onlyWithFeatures(self, *args):
        raise NotImplementedError('Abstract Method')

    def notLoadInputs(self, *args):
        raise NotImplementedError('Abstract Method')

    def getStyle(self, *args):
        raise NotImplementedError('Abstract Method')

    def setStyles(self, *args):
        raise NotImplementedError('Abstract Method')
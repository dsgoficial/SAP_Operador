from abc import ABC, abstractmethod

class IActivityInfoWidgetBuilder(ABC):
    
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def setMediator(self, *args):
        pass

    @abstractmethod
    def setDescription(self, *args):
        pass
    
    @abstractmethod
    def setNotes(self, *args):
        pass

    @abstractmethod
    def setRequirements(self, *args):
        pass

    @abstractmethod
    def setButtons(self):
        pass

    @abstractmethod
    def getResult(self):
        pass
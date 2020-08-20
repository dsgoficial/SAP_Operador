from abc import ABC, abstractmethod

class IActivityDataWidgetBuilder(ABC):
    
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def setMediator(self, *args):
        pass

    @abstractmethod
    def setStyles(self, *args):
        pass
  
    @abstractmethod
    def getResult(self):
        pass
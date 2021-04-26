from abc import ABC, abstractmethod

class IActivityDataWidgetBuilder(ABC):
    
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def setController(self, *args):
        pass
  
    @abstractmethod
    def getResult(self):
        pass
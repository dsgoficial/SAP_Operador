from abc import ABC, abstractmethod

class IActivityInputLinksWidgetBuilder(ABC):
    
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def setMediator(self, *args):
        pass

    @abstractmethod
    def setInputs(self, *args):
        pass
    
    
from abc import ABC, abstractmethod

class IActivityInputsWidgetBuilder(ABC):
    
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def setController(self, *args):
        pass

    @abstractmethod
    def setInputs(self, *args):
        pass
    
    
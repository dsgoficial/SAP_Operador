from abc import ABC, abstractmethod

class IActivityRoutinesWidgetBuilder(ABC):
    
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def setMediator(self, *args):
        pass

    @abstractmethod
    def setRoutines(self, *args):
        pass
    
    
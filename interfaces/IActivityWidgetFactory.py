from abc import ABC, abstractmethod

class IActivityWidgetFactory(ABC):
    
    @abstractmethod
    def makeActivityInfoWidget(self, *args):
        pass

    @abstractmethod
    def makeActivityDataWidget(self, *args):
        pass
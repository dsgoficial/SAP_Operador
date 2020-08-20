from abc import ABC, abstractmethod

class IProductionToolsBuilder(ABC):
    
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def addActivityWidget(self, *args):
        pass

    @abstractmethod
    def addLineageLabel(self, *args):
        pass

    @abstractmethod
    def getResult(self):
        pass
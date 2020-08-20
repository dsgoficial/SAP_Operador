
from abc import ABC, abstractmethod

class IProcessingFactory(ABC):
    
    @abstractmethod
    def createProcessing(self, *args):
       pass
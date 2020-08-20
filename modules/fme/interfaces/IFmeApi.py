from abc import ABC, abstractmethod

class IFmeApi(ABC):
    
    @abstractmethod
    def getSapRoutines(self, url): 
        pass
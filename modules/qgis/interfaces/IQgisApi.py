from abc import ABC, abstractmethod

class IQgisApi(ABC):
    
    @abstractmethod
    def getVersion(self):
        pass

    @abstractmethod
    def getPluginsVersions(self):
        pass
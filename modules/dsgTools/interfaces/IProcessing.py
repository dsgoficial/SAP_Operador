
from abc import ABC, abstractmethod

class IProcessing(ABC):

    @abstractmethod
    def run(self, *args):
       pass
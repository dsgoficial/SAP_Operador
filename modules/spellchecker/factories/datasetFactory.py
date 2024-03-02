from SAP_Operador.modules.spellchecker.datasets.ptBR import PtBR 
from SAP_Operador.modules.spellchecker.structures.ternarySearchTree import Trie

class DatasetFactory:

    def getDataset(self, dataset):
        methods = {
            'pt-BR': PtBR
        }
        return methods[dataset]()
from Ferramentas_Producao.modules.spellchecker.datasets.ptBR import PtBR 
from Ferramentas_Producao.modules.spellchecker.structures.ternarySearchTree import Trie

class DatasetFactory:

    def getDataset(self, dataset):
        methods = {
            'pt-BR': PtBR
        }
        return methods[dataset]()
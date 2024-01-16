from Ferramentas_Producao.modules.spellchecker.factories.datasetFactory import DatasetFactory 

class SpellCheckerCtrl:

    def __init__(self, dataset, datasetFactory=None):
        self.datasetFactory = DatasetFactory() if datasetFactory is None else datasetFactory
        self.dataset = DatasetFactory().getDataset(dataset)

    def hasWord(self, word):
        return self.dataset.hasWord(word)
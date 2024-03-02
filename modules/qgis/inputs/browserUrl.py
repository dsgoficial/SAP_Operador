from SAP_Operador.modules.qgis.inputs.inputData import InputData
import webbrowser

class BrowserUrl(InputData):

    def __init__(self):
        super(BrowserUrl, self).__init__()
    
    def load(self, fileData):
        for d in fileData:
            url = d['caminho']
            try:
                webbrowser.get('firefox').open(url)
            except:
                webbrowser.open(url)

        
        
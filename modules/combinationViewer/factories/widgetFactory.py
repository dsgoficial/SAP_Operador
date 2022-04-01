from Ferramentas_Producao.modules.combinationViewer.widgets.combinationViewerDlg import CombinationViewerDlg

class WidgetFactory:

    def createWidget(self, widgetName, *args):
        widgets = {
            'CombinationViewerDlg': CombinationViewerDlg
        }
        return widgets[widgetName](*args)
from SAP_Operador.modules.rasterMetadata.widgets.rasterMetadataDlg import RasterMetadataDlg

class WidgetFactory:

    def createWidget(self, widgetName, *args):
        widgets = {
            'RasterMetadataDlg': RasterMetadataDlg
        }
        return widgets[widgetName](*args)
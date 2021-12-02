from modules.pluginUpdater.widgets.messageDialog import MessageDialog

class GuiFactory:

    def create(self, widgetName, *args):
        widgets = {
            'MessageDialog': MessageDialog
        }
        return widgets[ widgetName ](*args) if widgetName in widgets else None
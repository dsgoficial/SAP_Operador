from modules.pluginUpdater.updaters.windowsUpdater import WindowsUpdater

class UpdaterFactory:

    def create(self, updaterName, *args):
        updaters = {
            'WindowsUpdater': WindowsUpdater
        }
        return updaters[ updaterName ](*args) if updaterName in updaters else None
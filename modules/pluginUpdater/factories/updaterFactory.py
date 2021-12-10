from modules.pluginUpdater.updaters.windowsUpdater import WindowsUpdater
from modules.pluginUpdater.updaters.linuxUpdater import LinuxUpdater

class UpdaterFactory:

    def create(self, updaterName, *args):
        updaters = {
            'WindowsUpdater': WindowsUpdater,
            'LinuxUpdater': LinuxUpdater
        }
        return updaters[ updaterName ](*args) if updaterName in updaters else None
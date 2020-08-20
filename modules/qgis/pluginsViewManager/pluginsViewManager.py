from PyQt5 import QtCore
from qgis.utils import plugins, iface
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

from Ferramentas_Producao.modules.qgis.interfaces.IPluginsViewManager import IPluginsViewManager

class PluginsViewManager(IPluginsViewManager):

    def __init__(self):
        super(PluginsViewManager, self).__init__()

    def getShortcutKey(self, shortcutKeyName):
        keys = {
            'Y': QtCore.Qt.Key_Y,
            'B': QtCore.Qt.Key_B,
        }
        if not shortcutKeyName in keys:
            return
        return keys[shortcutKeyName]

    def createAction(self, name, iconPath, shortcutKeyName, callback):
        a = QAction(
            QIcon(iconPath),
            name,
            iface.mainWindow()
        )
        if self.getShortcutKey(shortcutKeyName):
            a.setShortcut(self.getShortcutKey(shortcutKeyName))
        a.setCheckable(True)
        a.toggled.connect(callback)
        iface.digitizeToolBar().addAction(a)
        return a

    def deleteAction(self, action):
        iface.digitizeToolBar().removeAction(action)

    def addActionDigitizeToolBar(self, action):
        iface.digitizeToolBar().addAction(
            action
        )

    def removeActionDigitizeToolBar(self, action):
        iface.digitizeToolBar().removeAction(
            action
        )

    def addDockWidget(self, dockWidget, side):
        if side == 'right':
            iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)
        iface.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dockWidget)

    def removeDockWidget(self, dockWidget):
        if not dockWidget.isVisible():
            return
        iface.removeDockWidget(dockWidget)
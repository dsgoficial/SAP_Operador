from configparser import ConfigParser, Error as ConfigParserError
from qgis.core import QgsMessageLog, Qgis

class PluginCompatibility:
    """Verifica se um plugin do repositório declara suporte à versão do QGIS em execução.

    Segue a regra do gerenciador de plugins do QGIS: a versão atual (major.minor)
    precisa estar entre qgisMinimumVersion e qgisMaximumVersion; sem máximo
    declarado, o máximo é '<major do mínimo>.99'.
    """

    LOG_TAG = 'SAP Operador'

    def __init__(self, qgisVersion):
        self.qgisVersion = self.versionTuple(qgisVersion)

    def versionTuple(self, version):
        numbers = []
        for part in (version or '').strip().split('.'):
            digits = ''
            for char in part.strip():
                if not char.isdigit():
                    break
                digits += char
            if not digits:
                break
            numbers.append(int(digits))
        return tuple(numbers)

    def majorMinor(self, versionTuple):
        return (tuple(versionTuple) + (0, 0))[:2]

    def parseMetadata(self, metadataText):
        cp = ConfigParser(interpolation=None, strict=False)
        cp.read_string(metadataText)
        return cp['general']

    def isCompatible(self, pluginName, metadataText):
        if not self.qgisVersion:
            self.log('Versão do QGIS indefinida; plugin "{0}" ignorado pelo atualizador.'.format(pluginName))
            return False
        try:
            general = self.parseMetadata(metadataText or '')
        except (ConfigParserError, KeyError) as e:
            self.log('Plugin "{0}" ignorado pelo atualizador: metadata.txt ilegível ({1}).'.format(pluginName, e))
            return False
        minVersion = self.versionTuple(general.get('qgisMinimumVersion', '')) or (0,)
        maxVersion = self.versionTuple(general.get('qgisMaximumVersion', '')) or (minVersion[0], 99)
        current = self.majorMinor(self.qgisVersion)
        if self.majorMinor(minVersion) <= current <= self.majorMinor(maxVersion):
            return True
        self.log(
            'Plugin "{0}" ignorado pelo atualizador: feito para QGIS {1} a {2}, em execução {3}.'.format(
                pluginName,
                '.'.join(map(str, self.majorMinor(minVersion))),
                '.'.join(map(str, self.majorMinor(maxVersion))),
                '.'.join(map(str, self.qgisVersion))
            )
        )
        return False

    def log(self, message):
        QgsMessageLog.logMessage(message, self.LOG_TAG, Qgis.MessageLevel.Warning)

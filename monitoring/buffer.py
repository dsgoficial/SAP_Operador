import json

from SAP_Operador.modules.qgis.qgisApi import QgisApi

# Teto do buffer offline: numa queda longa de rede, descarta os mais antigos
# em vez de crescer o QSettings sem limite.
MAX_BUFFER = 1000


class MonitoringBuffer:
    """Buffer offline para os payloads de microcontrole.

    Guarda em QSettings os payloads que falharam ao serem enviados (sem rede)
    e os reenvia no proximo flush bem sucedido. Mantem por endpoint, usando a
    chave informada na criacao.
    """

    def __init__(self, key, qgis=None):
        self.key = key
        self.qgis = QgisApi() if qgis is None else qgis

    def _load(self):
        dumpData = self.qgis.getSettingsVariable(self.key)
        if not dumpData:
            return []
        try:
            data = json.loads(dumpData)
        except (ValueError, TypeError):
            return []
        return data if isinstance(data, list) else []

    def _save(self, payloads):
        self.qgis.setSettingsVariable(self.key, json.dumps(payloads))

    def add(self, payload):
        payloads = self._load()
        payloads.append(payload)
        if len(payloads) > MAX_BUFFER:
            payloads = payloads[-MAX_BUFFER:]
        self._save(payloads)

    def isEmpty(self):
        return not self._load()

    def flush(self, sender):
        """Tenta reenviar os payloads bufferizados.

        sender e uma funcao que recebe um payload e levanta excecao em caso de
        falha. Os payloads enviados com sucesso sao removidos do buffer; ao
        primeiro erro o reenvio para e os restantes ficam guardados.
        """
        payloads = self._load()
        if not payloads:
            return True
        remaining = list(payloads)
        for payload in payloads:
            try:
                sender(payload)
                remaining.pop(0)
            except Exception:
                break
        self._save(remaining)
        return not remaining

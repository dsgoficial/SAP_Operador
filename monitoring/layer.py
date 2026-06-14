from qgis.core import QgsVectorLayer, QgsWkbTypes, QgsFeatureRequest

from SAP_Operador.timers.timer import Timer
from SAP_Operador.monitoring.buffer import MonitoringBuffer

BUFFER_KEY = 'productiontools:monitoring:feicao:buffer'
FLUSH_INTERVAL = 30 * 1000


class Layer:
    """Captura de microcontrole por feicao de uma camada de producao.

    Acumula por camada as operacoes (insert, delete, update atributo, update
    geometria) e da flush no commit da camada e tambem em timer de 30s. Nunca
    envia operacao com quantidade zero. Se o envio falhar (sem rede), o payload
    e bufferizado em QSettings e reenviado no proximo flush bem sucedido.
    """

    def __init__(self, layer, activityId, sap):
        if not isinstance(layer, QgsVectorLayer):
            raise ValueError("layer must be a QgsVectorLayer instance")

        self.layer = layer
        self.activityId = activityId
        self.sap = sap
        # Nome da tabela e fixo para a camada; resolve uma vez (nao por flush).
        self.table = layer.dataProvider().uri().table()
        self.buffer = MonitoringBuffer(BUFFER_KEY)
        self.changed_ids = set()
        self.updated_length = {}
        self.updated_vertices = {}
        self.reset_counters()

        self.timer = Timer()
        self.timer.addCallback(self.flush)
        self.timer.start(FLUSH_INTERVAL)

        self.layer.geometryChanged.connect(self.on_geometry_change)
        self.layer.beforeCommitChanges.connect(self.before_commit_changes)
        self.layer.beforeRollBack.connect(self.on_rollback)
        self.layer.committedFeaturesAdded.connect(self.on_feature_added)
        self.layer.committedFeaturesRemoved.connect(self.on_features_deleted)
        self.layer.committedAttributeValuesChanges.connect(self.on_attribute_value_changed)
        self.layer.committedGeometriesChanges.connect(self.save_geometry_changed)
        # Um commit dispara varios sinais committed*; da flush UMA vez ao final
        # (afterCommitChanges), com todos os contadores ja acumulados e o delta
        # de geometria ja calculado em before_commit_changes. Evita varios POSTs
        # por commit e o reset que zerava o comprimento/vertices entre sinais.
        self.layer.afterCommitChanges.connect(self.flush)

    def reset_counters(self):
        self.deletes = 0
        self.inserts = 0
        self.updates = 0
        self.geom_updates = 0
        self.insert_length = 0
        self.insert_vertices = 0
        self.geom_length = 0
        self.geom_vertices = 0
        self.changed_ids = set()
        self.updated_length = {}
        self.updated_vertices = {}

    def on_geometry_change(self, featureId, newGeometry):
        self.changed_ids.add(featureId)
        self.updated_length[featureId] = newGeometry.length()
        self.updated_vertices[featureId] = len(list(newGeometry.vertices()))

    def before_commit_changes(self):
        data_provider = self.layer.dataProvider()
        for featureId in self.changed_ids:
            if featureId not in self.updated_length:
                continue
            try:
                original_feature = next(data_provider.getFeatures(QgsFeatureRequest(featureId)))
            except StopIteration:
                self.updated_length.pop(featureId, None)
                self.updated_vertices.pop(featureId, None)
                continue
            original_geom = original_feature.geometry()
            original_length = original_geom.length()
            original_vertices = len(list(original_geom.vertices()))
            self.geom_length += abs(self.updated_length[featureId] - original_length)
            self.geom_vertices += abs(self.updated_vertices[featureId] - original_vertices)
            self.updated_length.pop(featureId, None)
            self.updated_vertices.pop(featureId, None)
        self.changed_ids = set()

    def process_geometry(self, geom):
        num_vertices = 0
        length = 0
        geom_type = geom.type()
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            num_vertices += 1
        elif geom_type in (QgsWkbTypes.GeometryType.LineGeometry, QgsWkbTypes.GeometryType.PolygonGeometry):
            length += geom.length()
            num_vertices += len(list(geom.vertices()))
        return num_vertices, length

    def on_features_deleted(self, name, featureIds):
        self.deletes += len(featureIds)

    def on_feature_added(self, name, features):
        self.inserts += len(features)
        for feat in features:
            geom = feat.geometry()
            num_vertices, length = self.process_geometry(geom)
            self.insert_vertices += num_vertices
            self.insert_length += length

    def on_attribute_value_changed(self, name, features):
        self.updates += len(features.keys())

    def save_geometry_changed(self, name, features):
        self.geom_updates += len(features.keys())

    def on_rollback(self):
        self.reset_counters()

    def build_data(self):
        table = self.table
        dados = []
        if self.inserts > 0:
            dados.append({
                'tipo_operacao_id': 1,
                'quantidade': self.inserts,
                'comprimento': self.insert_length,
                'vertices': self.insert_vertices,
                'camada': table
            })
        if self.deletes > 0:
            dados.append({
                'tipo_operacao_id': 2,
                'quantidade': self.deletes,
                'camada': table
            })
        if self.updates > 0:
            dados.append({
                'tipo_operacao_id': 3,
                'quantidade': self.updates,
                'camada': table
            })
        if self.geom_updates > 0:
            dados.append({
                'tipo_operacao_id': 4,
                'quantidade': self.geom_updates,
                'comprimento': self.geom_length,
                'vertices': self.geom_vertices,
                'camada': table
            })
        return dados

    def _send(self, payload):
        self.sap.saveLayerTrack(payload)

    def flush(self):
        dados = self.build_data()
        if not dados:
            self.buffer.flush(self._send)
            return
        payload = {
            'atividade_id': self.activityId,
            'dados': dados
        }
        try:
            self._send(payload)
            self.reset_counters()
            self.buffer.flush(self._send)
        except Exception:
            self.buffer.add(payload)
            self.reset_counters()

    def disconnect_all_signals(self):
        try:
            self.flush()
        except (RuntimeError, AttributeError):
            pass
        self.timer.stop()
        for signal, slot in (
            (self.layer.geometryChanged, self.on_geometry_change),
            (self.layer.beforeCommitChanges, self.before_commit_changes),
            (self.layer.beforeRollBack, self.on_rollback),
            (self.layer.committedFeaturesAdded, self.on_feature_added),
            (self.layer.committedFeaturesRemoved, self.on_features_deleted),
            (self.layer.committedAttributeValuesChanges, self.on_attribute_value_changed),
            (self.layer.committedGeometriesChanges, self.save_geometry_changed),
            (self.layer.afterCommitChanges, self.flush),
        ):
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass

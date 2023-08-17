from qgis.core import QgsVectorLayer, QgsWkbTypes, QgsFeatureRequest
from qgis.PyQt.QtCore import QCoreApplication

class Layer:
    def __init__(
            self, 
            layer, 
            activityId,
            sap
        ):
        if not isinstance(layer, QgsVectorLayer):
            raise ValueError("layer must be a QgsVectorLayer instance")

        self.deletes = 0
        self.inserts = 0
        self.updates = 0
        self.geom_updates = 0
        self.length = 0
        self.num_vertices = 0
        self.layer = layer
        self.activityId = activityId
        self.sap = sap
        self.reset_counters()
        self.changed_ids = set()
        self.updated_length = {}
        self.updated_vertices = {}

        self.layer.geometryChanged.connect(self.on_geometry_change)
        self.layer.beforeCommitChanges.connect(self.before_commit_changes)

        # Signals for commit (save) and rollback
        self.layer.beforeRollBack.connect(self.on_rollback)
        self.layer.committedFeaturesAdded.connect(self.on_feature_added)
        self.layer.committedFeaturesRemoved.connect(self.on_features_deleted)
        self.layer.committedAttributeValuesChanges.connect(self.on_attribute_value_changed)
        self.layer.committedGeometriesChanges.connect(self.save_geometry_changed)

    def on_geometry_change(self, id, new_geometry):
        self.changed_ids.add(id)
        self.updated_length[id] = new_geometry.length()
        self.updated_vertices[id] = len(list(new_geometry.vertices()))
        print(self.changed_ids, self.updated_length, self.updated_vertices)

    def before_commit_changes(self):
        print('before_commit_changes')
        # Get the data provider
        data_provider = self.layer.dataProvider()

        for feature_id in self.changed_ids:
            # Get the feature from the layer
            feature = self.layer.getFeature(feature_id)
            
            # Calculate the length of the new geometry
            new_length = feature.geometry().length()

            # Get the original feature from the data provider
            original_feature = next(data_provider.getFeatures(QgsFeatureRequest(feature_id)))

            # Calculate the length of the original geometry
            original_geom = original_feature.geometry()
            original_length = original_geom.length()
            original_vertices = len(list(original_geom.vertices()))

            self.length += abs(self.updated_length[feature_id] - original_length)
            self.num_vertices += abs(self.updated_vertices[feature_id] - original_vertices)

            # Print the difference in lengths
            print(f'Difference in length for feature {feature_id}: {self.updated_length[feature_id] - original_length}')
            print(f'Difference in vertice for feature {feature_id}: {self.updated_vertices[feature_id] - original_vertices}')

            del self.updated_length[feature_id]
            del self.updated_vertices[feature_id]

    def reset_counters(self):
        print('reseted')
        self.deletes = 0
        self.inserts = 0
        self.updates = 0
        self.geom_updates = 0
        self.length = 0
        self.num_vertices = 0
        self.changed_ids = set()
        print('started with:', self.deletes, self.inserts, self.updates, self.geom_updates, self.length, self.num_vertices)

    def process_geometry(self, geom):
        num_vertices = 0
        length = 0
        geom_type = geom.type()
        geom_wkbtype = geom.wkbType()
        if geom_type == QgsWkbTypes.PointGeometry:
            num_vertices += 1
            length += 0
        elif geom_type in (QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry):
            length += geom.length()
            num_vertices += len(list(geom.vertices()))
            
        print('num_vertices total: ', num_vertices)
        print('length total: ', length)

        return num_vertices, length

    def on_features_deleted(self, name, featureIds):
        print('deletedFeatureIds: ', featureIds)
        self.deletes += len(featureIds)
        ok = self.send_post_request()
        self.reset_counters() if ok else ''


    def on_feature_added(self, name, features):
        print('insert: ', [f.id() for f in features])
        self.inserts += len(features)

        for feat in features:
            geom = feat.geometry()
            num_vertices, length = self.process_geometry(geom)
            self.num_vertices += num_vertices
            self.length += length

        ok = self.send_post_request()
        self.reset_counters() if ok else ''

    def on_attribute_value_changed(self, name, features):
        print('update: ', [f for f in features.keys()])
        self.updates += len(features.keys())
        ok = self.send_post_request()
        self.reset_counters() if ok else ''

    def save_geometry_changed(self, name, features):
        print('update: ', [f for f in features.keys()])
        self.geom_updates += len(features.keys())
        ok = self.send_post_request()
        self.reset_counters() if ok else ''

    def on_rollback(self):
        print('rollback')
        self.deletes = 0
        self.inserts = 0
        self.length = 0
        self.num_vertices = 0
        self.updates = 0
        self.geom_updates = 0
        self.changed_ids = set()

    def send_post_request(self):
        # data = {
        #     "deletes": self.deletes,
        #     "inserts": self.inserts,
        #     "updates": self.updates,
        #     "geom_updates": self.geom_updates,
        #     "length": self.length, 
        #     "num_vertices": self.num_vertices
        # }
        try:
            self.sap.saveLayerTrack({
                'atividade_id': self.activityId,
                'dados': [
                    {
                        'tipo_operacao_id': 1, #insert,
                        'quantidade': self.inserts,
                        'comprimento': self.length,
                        'vertices': self.num_vertices,
                        'camada': self.layer.dataProvider().uri().table()
                    },
                    {
                        'tipo_operacao_id': 2, #delete,
                        'quantidade': self.deletes,
                        'camada': self.layer.dataProvider().uri().table()
                    },
                    {
                        'tipo_operacao_id': 3, #update attribute,
                        'quantidade': self.updates,
                        'camada': self.layer.dataProvider().uri().table()
                    },
                    {
                        'tipo_operacao_id': 4, #update geom,
                        'quantidade': self.geom_updates,
                        'camada': self.layer.dataProvider().uri().table()
                    }
                ]
            })
            return True
        except Exception as e:
            print(str(e))
            return False

    def disconnect_all_signals(self):
        try:
            self.layer.beforeRollBack.disconnect(self.on_rollback)
            self.layer.committedFeaturesAdded.disconnect(self.on_feature_added)
            self.layer.committedFeaturesRemoved.disconnect(self.on_features_deleted)
            self.layer.committedAttributeValuesChanges.disconnect(self.on_attribute_value_changed)
            self.layer.committedGeometriesChanges.disconnect(self.save_geometry_changed)
            self.layer.geometryChanged.disconnect(self.on_geometry_change)
            self.layer.beforeCommitChanges.disconnect(self.before_commit_changes)

            print("All signals disconnected.")
        except TypeError as e:
            print(f"Error disconnecting signals: {e}")

# layer = QgsProject.instance().mapLayersByName('aer_aq060_a')[0]
# counter = LayerChangeCounter(layer)
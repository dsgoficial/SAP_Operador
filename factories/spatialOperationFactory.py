from Ferramentas_Producao.spatialVerification.operations.addFeatures import AddFeatures
from Ferramentas_Producao.spatialVerification.operations.changedGeometry import ChangedGeometry

class SpatialOperationFactory:

    def createOperation(self, spatialOperationName, qgis, workspaceWkt):
        spatialOperations = {
            'AddFeatures': AddFeatures,
            'ChangedGeometry': ChangedGeometry
        }
        return spatialOperations[ spatialOperationName ]( qgis, workspaceWkt )
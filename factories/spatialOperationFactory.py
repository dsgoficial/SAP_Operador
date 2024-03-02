from SAP_Operador.spatialVerification.operations.addFeatures import AddFeatures
from SAP_Operador.spatialVerification.operations.changedGeometry import ChangedGeometry

class SpatialOperationFactory:

    def createOperation(self, spatialOperationName, qgis, workspaceWkt):
        spatialOperations = {
            'AddFeatures': AddFeatures,
            'ChangedGeometry': ChangedGeometry
        }
        return spatialOperations[ spatialOperationName ]( qgis, workspaceWkt )
from SAP_Operador.spatialVerification.validateUserOperations import ValidateUserOperations

class SpatialVerificationFactory:

    def createVerification(self, spatialVerificationName, qgis ):
        spatialVerifications = {
            'ValidateUserOperations': ValidateUserOperations
        }
        return spatialVerifications[ spatialVerificationName ]( qgis )
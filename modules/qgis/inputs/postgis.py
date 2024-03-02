from SAP_Operador.modules.qgis.inputs.inputLayer import InputLayer
from SAP_Operador.modules.database.factories.databaseFactory import DatabaseFactory
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets

class Postgis(InputLayer):

    def __init__(self,
            databaseFactory=None
        ):
        super(Postgis, self).__init__()
        self.databaseFactory = DatabaseFactory() if databaseFactory is None else databaseFactory

    def getUri(self, 
            dbName, 
            dbSchema, 
            layerName, 
            dbHost, 
            dbPort, 
            dbUser, 
            dbPassword,
            workUnitGeometry,
            epsg
        ):
        return """dbname='{}' host={} port={} user='{}' password='{}' table="{}"."{}" (geom) sql={}""".format(
            dbName, 
            dbHost, 
            dbPort, 
            dbUser,
            dbPassword,
            dbSchema,
            layerName,
            "ST_INTERSECTS(geom, ST_TRANSFORM(ST_GEOMFROMEWKT('{0}'), {1}))".format(
                workUnitGeometry, 
                epsg
            )     
        )

    def isPrimaryKey(self, field, layer):
        return (
            field.name() == 'id' 
            or 
            'id_' in field.name() 
            or 
            field in layer.primaryKeyAttributes()
        )

    def loadValueMap(self, lyr, valueMap):
        attributes = [ item['attribute'] for item in valueMap]
        for i, field in enumerate(lyr.fields()):
            if self.isPrimaryKey(field, lyr):
                formConfig = lyr.editFormConfig()
                formConfig.setReadOnly(i, True)
                lyr.setEditFormConfig(formConfig)
                continue
            if not(field.name() in attributes):
                continue
            widgetSetup = core.QgsEditorWidgetSetup(
                'ValueMap',
                {'map': valueMap[attributes.index(field.name())]['valueMap']}
            )
            lyr.setEditorWidgetSetup(i, widgetSetup)
        return lyr
    
    def load(self, fileData):
        dbAddress, dbName, dbSchema, layerName = fileData['caminho'].split('/')
        dbHost, dbPort = dbAddress.split(':') 
        dbUser = fileData['usuario']
        dbPassword = fileData['senha']
        uri = self.getUri(
            dbName, 
            dbSchema, 
            layerName, 
            dbHost, 
            dbPort, 
            dbUser, 
            dbPassword,
            fileData['workUnitGeometry'],
            fileData['epsg']
        )
        layer = core.QgsProject.instance().addMapLayer(
            core.QgsVectorLayer(uri, layerName, "postgres"), 
            False
        )
        layer.setReadOnly(True)

        database = self.databaseFactory.createPostgres(
            dbName, 
            dbHost, 
            dbPort, 
            dbUser, 
            dbPassword
        )
        mapValues = database.getAttributeValueMap(layerName, dbSchema)
        self.loadValueMap(layer, mapValues)

        self.addMapLayer( layer )

    def addMapLayer(self, layer, position=1):
        group = self.getGroupLayer()
        group.insertLayer(position, layer)
        
        
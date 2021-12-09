from Ferramentas_Producao.modules.qgis.inputs.inputLayer import InputLayer
from Ferramentas_Producao.modules.database.factories.databaseFactory import DatabaseFactory
from qgis import core, gui, utils
from PyQt5 import QtCore, uic, QtWidgets

class Postgis(InputLayer):

    def __init__(self,
            databaseFactory=DatabaseFactory()
        ):
        super(Postgis, self).__init__()
        self.databaseFactory = databaseFactory

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
        print(fileData)
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
            True
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

        #self.addMapLayer( layer )
        
        
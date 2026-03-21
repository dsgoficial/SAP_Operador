
from collections import OrderedDict

from SAP_Operador.controllers.prodToolsCtrl import ProdToolsCtrl
from qgis import core, gui, utils

import os
import json

from SAP_Operador.postgresql import Postgresql
import psycopg2


class LocalProdToolsDockCtrl(ProdToolsCtrl):

    def __init__(
            self,
            sap,
            qgis,
            databaseFactory,
            processingFactoryDsgTools,
            fme,
            prodToolsSettings,
            toolFactoryDsgTools,
            pomodoro=None,
            guiFactory=None,
            spatialVerificationFactory=None,
            canvasMonitoring=None,
        ):
        super(LocalProdToolsDockCtrl, self).__init__(
            sap=sap,
            qgis=qgis,
            databaseFactory=databaseFactory,
            processingFactoryDsgTools=processingFactoryDsgTools,
            fme=fme,
            prodToolsSettings=prodToolsSettings,
            toolFactoryDsgTools=toolFactoryDsgTools,
            pomodoro=pomodoro,
            guiFactory=guiFactory,
            spatialVerificationFactory=spatialVerificationFactory,
            canvasMonitoring=canvasMonitoring,
        )

    def authUser(self, dbusername, dbpassword, dbhost, dbport, dbnam):
        pg = Postgresql(dbnam, dbusername, dbhost, dbport, dbpassword)
        try:
            pg.execute(
                '''
                    SELECT * FROM public.sap_local;
                ''',
                ()
            )
        except psycopg2.errors.UndefinedTable:
            raise Exception('Tabela "public.sap_local" não existe!')
        result = pg.execute(
            '''
                SELECT count(*) FROM public.sap_local;
            ''',
            ()
        )
        if result[0][0] == 0:
            raise Exception('Não há dados na tabela "public.sap_local"!')
        return True

    def reload(self):
        #self.prodToolsSettings.checkPluginUpdates()
        if self.productionTools is None:
            return
        self.removeDock()
        self.sapActivity = self.sap.getActivity()
        if self.sapActivity is None:
            return
        self.loadShortcuts()
        self.productionTools = self.guiFactory.makeRemoteProductionToolsDock(self, self.productionTools)
        self.qgis.addDockWidget(self.productionTools, side='left')

    def loadDockWidget(self, dbusername, dbpassword, dbhost, dbport, dbname):
        pg = Postgresql(dbname, dbusername, dbhost, dbport, dbpassword)
        result = pg.execute(
            '''
                SELECT json_atividade FROM public.sap_local;
            ''',
            ()
        )
        activityData = json.loads(result[0][0])
        activityData['local_db']['password'] = dbpassword
        activityData['local_db']['username'] = dbusername
        activityData['local_db']['host'] = dbhost
        activityData['local_db']['port'] = dbport
        activityData['local_db']['database'] = dbname
        self.sapActivity = self.sap.getActivity(activityData)
        self.loadShortcuts()
        #self.loadChangeStyleTool( self.sapActivity.getStylesName() )
        self.productionTools = self.guiFactory.makeLocalProductionToolsDock(self)
        self.qgis.addDockWidget(self.productionTools, side='left')
        #self.prodToolsSettings.checkPluginUpdates()
        return self.productionTools

    def showEndActivityDialog(self):
        if self.qgis.hasModifiedLayers():
            self.showInfoMessageBox(
                self.productionTools,
                'Aviso',
                'Salve todas suas alterações antes de finalizar!'
            )
            return

        stepTypeId = self.sapActivity.getStepTypeId()
        noteLayers = self.sapActivity.getNoteLayers()
        try:
            checkStep = self.qgis.checkModifiedLayersByStepId(
                stepTypeId,
                noteLayers
            )
        except Exception as e:
            self.showErrorMessageBox( self.productionTools, 'Erro', str(e) )
            return
        if stepTypeId == 3 and checkStep:
            self.showInfoMessageBox(
                self.productionTools,
                'Aviso',
                'Existem apontamentos não resolvidos!'
            )
            return
        withoutCorrection = stepTypeId == 2 and checkStep
        result = self.sap.showEndActivityDialog(withoutCorrection)
        if not result:
            return
        #self.resetProject()

    def loadActivityLayers(self):
        scale = self.sapActivity.getScale()
        self.qgis.setProjectVariable('escala', int(scale.split(':')[-1]), encrypt=False)
        self.qgis.setProjectVariable('productiontools_scale', int(scale.split(':')[-1]), encrypt=False)
        loadLayersFromPostgis = self.processingFactoryDsgTools.createProcessing('LoadLayersFromPostgis', self)
        result = loadLayersFromPostgis.run({
            'dbName' : self.sapActivity.getDatabaseName(),
            'dbHost' : self.sapActivity.getDatabaseServer(),
            'layerNames' : self.getActivityLayerNames(),
            'dbPassword' : self.sapActivity.getDatabasePassword(),
            'dbPort' : self.sapActivity.getDatabasePort(),
            'dbUser' : self.sapActivity.getDatabaseUserName()
        })
        loadedLayerIds = result['OUTPUT']

        assingFilterToLayers = self.processingFactoryDsgTools.createProcessing('AssingFilterToLayers', self)
        assingFilterToLayers.run({'layers': self.sapActivity.getLayers()})

        groupLayers = self.processingFactoryDsgTools.createProcessing('GroupLayers', self)
        groupLayers.run({'layerIds': loadedLayerIds})

        defaultStyle = self.getActivityStyles()[0] if self.getActivityStyles() else None
        if defaultStyle:
            self.qgis.loadMapLayerStyles(
                loadedLayerIds,
                self.sapActivity.getLayerStyles(),
                defaultStyle
            )
            #self.changeStyleWidget.loadStyles(self.getActivityStyles(), defaultStyle)

        """ matchAndApplyQmlStylesToLayers = self.processingFactoryDsgTools.createProcessing('MatchAndApplyQmlStylesToLayers', self)
        matchAndApplyQmlStylesToLayers.run({
            'layersQml': self.sapActivity.getLayersQml(styleName),
            'layerIds': loadedLayerIds
        }) """

        assignValueMapToLayers = self.processingFactoryDsgTools.createProcessing('AssignValueMapToLayers', self)
        database = self.getActivityDatabase()
        assignValueMapToLayers.run({
            'valueMaps': {
                    layer["nome"]: database.getAttributeValueMap(layer["nome"], layer["schema"])
                    for layer in self.sapActivity.getLayers()
            },
            'layerIds': loadedLayerIds
        })

        assignMeasureColumnToLayers = self.processingFactoryDsgTools.createProcessing('AssignMeasureColumnToLayers', self)
        assignMeasureColumnToLayers.run({'layerIds': loadedLayerIds})

        assignAliasesToLayers = self.processingFactoryDsgTools.createProcessing('AssignAliasesToLayers', self)
        assignAliasesToLayers.run({
            'aliases': self.sapActivity.getLayerALiases(),
            'layerIds': loadedLayerIds
        })

        assignActionsToLayers = self.processingFactoryDsgTools.createProcessing('AssignActionsToLayers', self)
        assignActionsToLayers.run({
            'actions': self.sapActivity.getLayerActions(),
            'layerIds': loadedLayerIds
        })
        rules = self.sapActivity.getRules()
        if rules:
            assignFormatRulesToLayers = self.processingFactoryDsgTools.createProcessing('AssignFormatRulesToLayers', self)
            assignFormatRulesToLayers.run({
                'rules': rules,
                'layerIds': loadedLayerIds
            })

        """ assignConditionalStyleToLayers = self.processingFactoryDsgTools.createProcessing('AssignConditionalStyleToLayers', self)
        assignConditionalStyleToLayers.run({
            'conditionals': self.sapActivity.getLayerConditionalStyle(),
            'layerIds': loadedLayerIds
        }) """

        # setRemoveDuplicateNodePropertyOnLayers = self.processingFactoryDsgTools.createProcessing('SetRemoveDuplicateNodePropertyOnLayers', self)
        # setRemoveDuplicateNodePropertyOnLayers.run({'layerIds': loadedLayerIds})

        frameQuery = self.sapActivity.getFrameQuery()
        if not self.frameLoaded( frameQuery ):
            self.qgis.loadInputData({
                'query': self.sapActivity.getFrameQuery(),
                'epsg': self.sapActivity.getEPSG(),
                'nome': 'moldura',
                'tipo_insumo_id': 100,
                'qml': self.sapActivity.getFrameQml()
            })

        self.qgis.loadLayerActions(loadedLayerIds)

        self.qgis.setPrimaryKeyReadOnly( loadedLayerIds, True )

        if self.sapActivity.getStepTypeId() == 3:
            mapLayerIdNote = {}
            noteLayers = self.sapActivity.getNoteLayers()
            for layerNote in noteLayers:
                layerId = next(filter(lambda layerId: layerNote['nome'] in layerId, loadedLayerIds) , None)
                mapLayerIdNote[layerId] = layerNote
            noteLayerIds = mapLayerIdNote.keys()
            loadedNotelayers = self.qgis.getLayerFromIds(noteLayerIds)
            for layer in loadedNotelayers:
                note = mapLayerIdNote[layer.id()]
                self.qgis.setFieldsReadOnly(
                    [layer.id()],
                    [
                        n
                        for n in layer.fields().names()
                        if not(n == note['atributo_justificativa_apontamento'] or n == note['atributo_situacao_correcao'])
                    ],
                    True
                )

        if self.sapActivity.getStepTypeId() == 2:
            self.qgis.loadDefaultFieldValue(
                loadedLayerIds,
                [
                    {
                        'name': 'subfase_id',
                        'value': self.sapActivity.getSubphaseId()
                    }
                ]
            )
            self.qgis.setFieldsReadOnly( loadedLayerIds, ['subfase_id'], True )

        self.prodToolsSettings.initSaveTimer()

        self.validateUserOperations.setWorkspaceWkt( self.sapActivity.getFrameWkt() )
        self.validateUserOperations.setTraceableLayerIds( loadedLayerIds )
        self.validateUserOperations.start()
        self.canvasMonitoring.start()

        self.loadReviewTool()

        loadThemes = self.processingFactoryDsgTools.createProcessing('LoadThemes', self)
        for theme in self.sapActivity.getThemes():
            loadThemes.run({'themes': theme['definicao_tema']})
        self.sortLayersOnMolduraGroup()

    def sortLayersOnMolduraGroup(self):
        utils.iface.mapCanvas().freeze(True)
        rootNode = core.QgsProject.instance().layerTreeRoot()
        oldGroup = rootNode.findGroup('MOLDURA_E_INSUMOS')
        newGroup = rootNode.addGroup('MOLDURA_E_INSUMOS')
        auxDict = OrderedDict(
            {
                core.QgsWkbTypes.GeometryType.PointGeometry: [],
                core.QgsWkbTypes.GeometryType.LineGeometry: [],
                core.QgsWkbTypes.GeometryType.PolygonGeometry: [],
            }
        )
        rasterList = []
        for layerTreeView in oldGroup.children():
            lyr = layerTreeView.layer()
            if isinstance(lyr, core.QgsRasterLayer):
                rasterList.append(layerTreeView)
                continue
            if lyr.name() in ("aux_grid_revisao_a", "moldura"):
                idx = 0 if lyr.name() == "aux_grid_revisao_a" else -1
                myClone = layerTreeView.clone()
                newGroup.insertChildNode(idx, myClone)
                oldGroup.removeChildNode(layerTreeView)
                continue
            auxDict[lyr.geometryType()].append(layerTreeView)
        for geomType, layerTreeViewList in auxDict.items():
            for layerTreeView in sorted(layerTreeViewList, key=lambda x: x.layer().name(), reverse=False):
                myClone = layerTreeView.clone()
                newGroup.insertChildNode(-1, myClone)
                oldGroup.removeChildNode(layerTreeView)
        for rasterNode in sorted(rasterList, key=lambda x: x.layer().name().lower(), reverse=False):
            myClone = rasterNode.clone()
            newGroup.insertChildNode(-1, myClone)
            oldGroup.removeChildNode(rasterNode)
        rootNode.removeChildNode(oldGroup)
        utils.iface.mapCanvas().freeze(False)

    def readProjectCallback(self):
        self.prodToolsSettings.initSaveTimer()
        self.canvasMonitoring.start()

    def createProjectCallback(self):
        self.canvasMonitoring.stop()

    def loadReviewTool(self):
        frameQuery = self.sapActivity.getFrameQuery()
        if not self.frameLoaded(frameQuery):
            self.qgis.loadInputData({
                'query': self.sapActivity.getFrameQuery(),
                'epsg': self.sapActivity.getEPSG(),
                'nome': 'moldura',
                'tipo_insumo_id': 100,
                'qml': self.sapActivity.getFrameQml()
            })
        loadLayersFromPostgis = self.processingFactoryDsgTools.createProcessing('LoadLayersFromPostgis', self)
        gridCandidateList = core.QgsProject.instance().mapLayersByName('aux_grid_revisao_a')
        if not gridCandidateList:
            result = loadLayersFromPostgis.run({
                'dbName': self.sapActivity.getDatabaseName(),
                'dbHost': self.sapActivity.getDatabaseServer(),
                'layerNames': ['aux_grid_revisao_a'],
                'dbPassword': self.sapActivity.getDatabasePassword(),
                'dbPort': self.sapActivity.getDatabasePort(),
                'dbUser': self.sapActivity.getDatabaseUserName()
            })
            loadedLayerIds = result['OUTPUT']
            if not loadedLayerIds:
                return
            gridLayer = core.QgsProject.instance().mapLayer(loadedLayerIds[0])
        else:
            gridLayer = gridCandidateList[0]

        # Check for field existence and build appropriate filter
        fields = [field.name() for field in gridLayer.fields()]
        has_new_fields = 'unidade_trabalho_id' in fields and 'etapa_id' in fields

        if has_new_fields:
            filter_expr = f'unidade_trabalho_id = {self.sapActivity.getWorkUnitId()} AND etapa_id = {self.sapActivity.getStepId()}'
        else:
            # Fall back to old atividade_id filter
            filter_expr = f'atividade_id = {self.sapActivity.getId()}'

        assingFilterToLayers = self.processingFactoryDsgTools.createProcessing('AssingFilterToLayers', self)
        assingFilterToLayers.run({
            'layers': [
                {
                    'filter': filter_expr,
                    'nome': 'aux_grid_revisao_a',
                    'schema': gridLayer.dataProvider().uri().schema()
                }
            ]
        })

        self.moveLayerToGroup(gridLayer.id())

        reviewToolBar = self.toolFactoryDsgTools.getTool('ReviewToolBar', self)
        if gridLayer.featureCount() != 0:
            reviewToolBar.run(gridLayer)
            return

        createReviewGrid = self.processingFactoryDsgTools.createProcessing('CreateReviewGrid', self)
        scale = self.sapActivity.getScale()
        frameLyr = core.QgsProject.instance().mapLayersByName('moldura')[0]

        # Determine grid size based on scale
        if int(scale.split(':')[-1]) <= 10000:
            param = {
                'input': frameLyr,
                'x_grid_size': (0.001) if frameLyr.crs().isGeographic() else (1e2),
                'y_grid_size': (0.001) if frameLyr.crs().isGeographic() else (1e2)
            }
        else:
            param = {
                'input': frameLyr,
                'x_grid_size': (0.01) if frameLyr.crs().isGeographic() else (1e3),
                'y_grid_size': (0.008) if frameLyr.crs().isGeographic() else (800)
            }

        # Add appropriate IDs based on field existence
        if has_new_fields:
            param.update({
                'unit_work_id': self.sapActivity.getWorkUnitId(),
                'step_id': self.sapActivity.getStepId()
            })
        else:
            param['related_task_id'] = self.sapActivity.getId()

        result = createReviewGrid.run(param)
        outputLayer = result['OUTPUT']
        reviewToolBar.run(gridLayer, outputLayer=outputLayer)

    def moveLayerToGroup(self, loadedLayerId, positionToInsert=0):
        utils.iface.mapCanvas().freeze(True)
        rootNode = core.QgsProject.instance().layerTreeRoot()
        group = rootNode.findGroup('MOLDURA_E_INSUMOS')
        lyrNode = rootNode.findLayer(loadedLayerId)
        myClone = lyrNode.clone()
        group.insertChildNode(positionToInsert, myClone)
        rootNode.removeChildNode(lyrNode)
        utils.iface.mapCanvas().freeze(False)

    def saveControllerInfo(self, user, userID, startTime, endTime):
        pg = Postgresql(
            self.sapActivity.getDatabaseName(),
            self.sapActivity.getDatabaseUserName() ,
            self.sapActivity.getDatabaseServer(),
            self.sapActivity.getDatabasePort(),
            self.sapActivity.getDatabasePassword()
        )
        pg.execute(
            '''
                UPDATE public.sap_local
                SET
                    nome_usuario = %s,
                    usuario_uuid = %s,
                    data_inicio = %s,
                    data_fim = %s
                RETURNING *;
            ''',
            (
                user, userID, startTime, endTime
            )
        )

    def getControllerInfo(self):
        pg = Postgresql(
            self.sapActivity.getDatabaseName(),
            self.sapActivity.getDatabaseUserName() ,
            self.sapActivity.getDatabaseServer(),
            self.sapActivity.getDatabasePort(),
            self.sapActivity.getDatabasePassword()
        )
        result = pg.execute(
            '''
                SELECT
                    EXTRACT (EPOCH FROM data_inicio),
                    EXTRACT (EPOCH FROM data_fim),
                    nome_usuario,
                    usuario_uuid
                FROM public.sap_local;
            ''',
            ()
        )
        return result[0]

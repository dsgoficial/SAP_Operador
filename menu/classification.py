#! -*- coding: utf-8 -*-
from qgis import core, gui
from qgis.core import QgsEditFormConfig
from PyQt4 import QtCore, QtGui
import re, sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from managerLoadLayers.loadLayers import LoadLayers
from managerQgis.projectQgis import ProjectQgis
from menu_forms import Menu_forms 

class Classification(QtCore.QObject):

    showMessageErro = QtCore.pyqtSignal(str)
    activeAcquisitionTool = QtCore.pyqtSignal(str)
    
    def __init__(self, iface, data, dbJson):
        # construtor
        super(Classification, self).__init__()
        self.iface = iface
        self.data = data
        self.loadLayers = LoadLayers(iface, data)
        self.dbJson = dbJson
        self.idBefore = 0
        self.userForm = Menu_forms()
        self.connectionData = None 
        self.menuData = None 
        self.currentButtonMenu = None 
        self.currentLayer = None
        self.reclassificationData = None
        self.projectQgis = ProjectQgis(self.iface)

    def startSignals(self):
        iface = self.iface
        iface.actionAddFeature().toggled.connect(self.disconnectLayer)
        iface.layerTreeView().clicked.connect(self.disconnectLayer)
        iface.legendInterface().itemAdded.connect(self.disconnectLayer)
        iface.actionToggleEditing().triggered.connect(self.disconnectLayer)
    
    def stopSignals(self):
        iface = self.iface
        try:
            iface.actionAddFeature().toggled.disconnect(self.disconnectLayer)
        except:
            pass
        try:
            iface.layerTreeView().clicked.disconnect(self.disconnectLayer)
        except: 
            pass
        try:
            iface.legendInterface().itemAdded.disconnect(self.disconnectLayer)
        except:
            pass
        try:
            iface.actionToggleEditing().triggered.disconnect(self.disconnectLayer)
        except:
            pass

    def disconnectLayer(self):
        currentLayer = self.iface.activeLayer()
        if currentLayer and (currentLayer.type() == core.QgsMapLayer.VectorLayer):
            self.activateFormQgis(currentLayer)
            for function in [
                                self.createFeatureWithForm, 
                                self.createFeatureWithoutForm
                            ]:
                try:
                    currentLayer.featureAdded.disconnect(function)
                except:
                    pass

    def formatLayerData(self, lyrName):
        layerSelectedFormated = {}
        groupGeom = {'a' : 'AREA', 
                     'c' : 'PONTO',
                     'p' : 'PONTO', 
                     'd' : 'LINHA',
                     'l' : 'LINHA',
        }
        group = groupGeom[lyrName.split('_')[-1]]
        layerSelectedFormated[group] = {}
        catLayer = lyrName.split('_')[0]
        layerSelectedFormated[group][catLayer] = []
        layerSelectedFormated[group][catLayer].append(lyrName)
        return layerSelectedFormated  

    def getLayer(self):
        layerName = self.currentButtonMenu.buttonData['formValues'][u'*Selecione camada:']
        layer = self.getLayerByName(layerName)
        if layer:
            return layer
        self.addLayerOnCanvas(layerName)
        return self.getLayer()

    def getLayerByName(self, lyrName):
        dbname = self.connectionData['dbname']
        result = core.QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in result:
            uriClass = core.QgsDataSourceURI(layer.styleURI())
            test = (
                (dbname == layer.source().split(' ')[0][8:-1]) and
                (lyrName == uriClass.table())
            )
            if test:
                self.iface.setActiveLayer(layer)
                return layer
        return False

    def addLayerOnCanvas(self, lyrName):
        self.loadLayers.loadAllLayersSelected({
            'activeProgressBar' : False,
            'layersSelected' : [lyrName],
            'layersSelectedFormated' : self.formatLayerData(lyrName),
            'dbAlias' : self.menuData['dbname'],
            'workspace' : self.menuData['workspace'],
            'styleName' : self.menuData['stylename'],
            'selectedRulesType' : '',
            'dbJson' : self.dbJson,
        })
        
    def removeSelectedLayers(self):
        mapCanvas = self.iface.mapCanvas()
        for lyr in mapCanvas.layers():
            if lyr.type() == core.QgsMapLayer.VectorLayer:
                lyr.removeSelection()
         
    def removeSelectedByLayerName(self, layerName):
        result = core.QgsMapLayerRegistry.instance().mapLayersByName(layerName)
        for lyr in result:
            if lyr.type() == core.QgsMapLayer.VectorLayer:
                lyr.removeSelection()
           
    def validateSelected(self):
        selected = {}
        dbname = self.connectionData['dbname']
        currentLayer = self.currentLayer
        mapCanvas = self.iface.mapCanvas()
        for lyr in mapCanvas.layers():
            test1 = (
                lyr and 
                (lyr.type() == core.QgsMapLayer.VectorLayer) and 
                (lyr.selectedFeatureCount() > 0) and 
                (
                    currentLayer.geometryType() != lyr.geometryType() or
                    dbname != lyr.source().split(' ')[0][8:-1]
                )
            )
            test2 = (
                lyr and 
                (lyr.type() == core.QgsMapLayer.VectorLayer) and 
                (lyr.selectedFeatureCount() > 0)
            )
            if test1:
                message =  u"<p style='color: red;'>\
                        Erro: Não é possível reclassificar feições de\
                        geometrias diferentes ou de banco de dados diferentes!\
                        </p>\
                        <p style='color: blue;'>\
                        Solução: Selecione feições de mesmo tipo geométrico\
                        ou de um mesmo banco de dados\
                        </p>"
                self.showMessageErro.emit(message)
                return {}
            elif test2:
                lyrName = lyr.name()
                selectedIds = lyr.selectedFeaturesIds()
                selected[lyrName] = selectedIds
        return selected
        
    def run(self, button, activeReclass, connectionData, menuData):
        self.currentButtonMenu =  button
        self.connectionData = connectionData
        self.menuData = menuData
        currentLayer = self.getLayer()   
        self.currentLayer = currentLayer
        if activeReclass:
            lyrsSelected = self.validateSelected()
            if lyrsSelected:
                self.userForm.ok.connect(self.cutPasteOrUpdateFeatures)
                self.userForm.ok.connect(self.userForm.close)
                self.userForm.createFormConfirmReclassification(button, lyrsSelected)
                self.userForm.exec_()
        self.addFeature()

    def deactivateFormQgis(self, currentLayer):
        currentLayer.editFormConfig().setSuppress(QgsEditFormConfig.SuppressOn)
        currentLayer.setFeatureFormSuppress(True)

    def activateFormQgis(self, currentLayer):
        currentLayer.editFormConfig().setSuppress(QgsEditFormConfig.SuppressOff)
        currentLayer.setFeatureFormSuppress(False)
        
    def cutPasteOrUpdateFeatures(self, formValues, fields):
        self.reclassificationData = formValues
        currentLayer =  self.currentLayer
        currentLayer.startEditing()
        currentLayer.featureAdded.connect(self.reclassifyFeatures)
        iface = self.iface 	
        iface.actionAddFeature().trigger()
        self.deactivateFormQgis(currentLayer)
        for lyrName in fields:
            if formValues[u'{0}_cbx'.format(lyrName)]:
                beforeLayer = self.getLayerByName(lyrName)
                if beforeLayer:
                    iface.setActiveLayer(beforeLayer)
                    if lyrName == currentLayer.name():
                        ids = fields[lyrName]
                        feats = self.getFeaturesByIds(ids)
                        for feat in feats:
                            self.updateFeature(feat)
                    else:
                        iface.actionCutFeatures().trigger()
                        iface.setActiveLayer(currentLayer)
                        iface.actionPasteFeatures().trigger()
        currentLayer.endEditCommand()
        try:
            currentLayer.featureAdded.disconnect(self.reclassifyFeatures)
        except:
            pass
        iface.activeLayer().removeSelection()
    
    def getFeaturesByIds(self, ids):
        feats = []
        for feat in self.iface.activeLayer().getFeatures():
            if feat.id() in ids:
                feats.append( feat )
        return feats

    def updateFeature(self, feat):
        f = feat
        lyr = self.currentLayer
        fields = self.reclassificationData
        for field in fields:
            indx = lyr.fieldNameIndex(unicode(field))
            if indx >= 0 : 
                valueMap = lyr.valueMap(indx)
                isLineEdit = (
                    lyr.editorWidgetV2(indx) == u'TextEdit' or
                    lyr.editorWidgetV2(indx) == u'UniqueValues'
                )
                isValueMap = (
                    (lyr.editorWidgetV2(indx) == u'ValueMap') and 
                    ( fields[field] in valueMap)
                )
                if isLineEdit and fields[field] and fields[field] != u"NULL":
                    value  = fields[field]
                    if re.match('^\@value\(".+"\)$', value):
                        variable = value.split('"')[-2]
                        value = self.projectQgis.getVariableProject(variable)
                    lyr.changeAttributeValue(
                        f.id(), 
                        indx , 
                        value
                    )    
                elif isValueMap:
                    lyr.changeAttributeValue(
                        f.id(), 
                        indx, 
                        valueMap[fields[field]]
                    ) 

    def reclassifyFeatures(self, i):
        lyr = self.currentLayer
        editBuffer = lyr.editBuffer()
        if i in editBuffer.addedFeatures():
            f = editBuffer.addedFeatures()[i]
            fields = self.reclassificationData
            for field in fields:
                indx = lyr.fieldNameIndex(unicode(field))
                if indx >= 0 : 
                    valueMap = lyr.valueMap(indx)
                    isLineEdit = (
                        lyr.editorWidgetV2(indx) == u'TextEdit' or
                        lyr.editorWidgetV2(indx) == u'UniqueValues'
                    )
                    isValueMap = (
                        (lyr.editorWidgetV2(indx) == u'ValueMap') and 
                        ( fields[field] in valueMap)
                    )
                    if isLineEdit and fields[field] and fields[field] != u"NULL":
                        value  = fields[field]
                        if re.match('^\@value\(".+"\)$', value):
                            variable = value.split('"')[-2]
                            value = self.projectQgis.getVariableProject(variable)
                        lyr.changeAttributeValue(
                            f.id(), 
                            indx , 
                            value
                        )    
                    elif isValueMap:
                        lyr.changeAttributeValue(
                            f.id(), 
                            indx, 
                            valueMap[fields[field]]
                        ) 
    
    def activeAcquisitionTool(self, acquisitionToolName):
        if  acquisitionToolName == u'Mão livre':
            self.activeToolByName(u'DSGTools: Ferramenta de aquisição mão livre')
        elif acquisitionToolName == u'Angulor reto':  
            self.activeToolByName(u'DSGTools: Ferramenta de aquisição com ângulos retos')  
        elif acquisitionToolName ==  u'Circulo':
            self.activeToolByName(u'DSGTools: Ferramenta de Aquisição de Círculos')

    def activeToolByName(self, toolName):
        for a in self.iface.mainWindow().findChildren(QtGui.QToolBar):
            if a.objectName() == u'DsgTools':
                for action in a.actions():
                    if toolName == action.text():
                        action.trigger() 

    def addFeature(self):
        self.currentLayer.beginEditCommand("start menu")
        self.currentLayer.startEditing()
        self.iface.actionAddFeature().trigger()
        self.activeAcquisitionTool(
            self.currentButtonMenu.buttonData['formValues'][u'Escolha ferramenta de aquisição:']
        )
        self.deactivateFormQgis(self.currentLayer)
        closeForm = self.currentButtonMenu.buttonData['formValues'][u'Fechar form na aquisição:']
        if closeForm.lower() == u'sim':
            self.currentLayer.featureAdded.connect(self.createFeatureWithoutForm)
        else:
            self.currentLayer.featureAdded.connect(self.createFeatureWithForm)

    def createFeatureWithForm(self, i):
        lyr = self.currentLayer
        if i < 0 and i != self.idBefore:
            self.idBefore = i
            self.iface.activeLayer().removeSelection()
            lyr.select(i) 
            f = lyr.selectedFeatures()[0]
            lyr.deselect(i)
            attrDialog = gui.QgsAttributeDialog(lyr, f, False)
            fields = self.currentButtonMenu.buttonData['formValues']
            for field in fields:
                indx = lyr.fieldNameIndex(unicode(field))
                if indx >0:
                    valueMap = lyr.valueMap(indx)
                    isLineEdit = (
                        lyr.editorWidgetV2(indx) == u'TextEdit' or
                        lyr.editorWidgetV2(indx) == u'UniqueValues'
                    )
                    isValueMap = (
                        (lyr.editorWidgetV2(indx) == u'ValueMap') and 
                        ( fields[field] in valueMap)
                    )
                    if isValueMap:
                        attrDialog.attributeForm().changeAttribute(
                                field , valueMap[fields[field]]
                            )
                    elif isLineEdit and fields[field] and fields[field] != u"NULL":
                        value  = fields[field]
                        if re.match('^\@value\(".+"\)$', value):
                            variable = value.split('"')[-2]
                            value = self.projectQgis.getVariableProject(variable)
                        attrDialog.attributeForm().changeAttribute(
                                field , value         
                            )
            result = attrDialog.exec_()
            lyr.endEditCommand()
            if not result:
                lyr.deleteFeature(i)
                self.iface.mapCanvas().refresh()  

    def createFeatureWithoutForm(self, i):
        lyr = self.currentLayer
        editBuffer = lyr.editBuffer()
        if i in editBuffer.addedFeatures() and i != self.idBefore:
            self.idBefore = i
            self.iface.activeLayer().removeSelection()
            lyr.select(i)
            f = lyr.selectedFeatures()[0]
            lyr.deselect(i)
            fields = self.currentButtonMenu.buttonData['formValues']
            for field in fields:
                indx = lyr.fieldNameIndex(unicode(field))
                if indx >= 0 : 
                    valueMap = lyr.valueMap(indx)
                    isLineEdit = (
                        lyr.editorWidgetV2(indx) == u'TextEdit' or
                        lyr.editorWidgetV2(indx) == u'UniqueValues'
                    )
                    isValueMap = (
                        (lyr.editorWidgetV2(indx) == u'ValueMap') and 
                        ( fields[field] in valueMap)
                    )
                    if isLineEdit and fields[field] and fields[field] != u"NULL":
                        value  = fields[field]
                        if re.match('^\@value\(".+"\)$', value):
                            variable = value.split('"')[-2]
                            value = self.projectQgis.getVariableProject(variable)
                        lyr.changeAttributeValue(
                            f.id(), 
                            indx , 
                            value
                        )                   
                    elif isValueMap:
                        lyr.changeAttributeValue(
                            f.id(), 
                            indx, 
                            valueMap[fields[field]]
                        )
            lyr.endEditCommand()

    
                    
    
                
                

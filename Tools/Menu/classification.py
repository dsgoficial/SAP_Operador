#! -*- coding: utf-8 -*-
from qgis import core, gui
from qgis.core import QgsEditFormConfig
from PyQt5 import QtCore, QtGui, QtWidgets
import re, sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))

class Classification(QtCore.QObject):

    reclassify_form = QtCore.pyqtSignal(dict, dict)
    
    def __init__(self, iface):
        super(Classification, self).__init__()
        self.iface = iface
        self.settings = {}
        self.layer_vector = {}
        self.fid_before = None
        self.with_form = None
        self.ignore = False
        self.current_button_layer = None
        self.current_button_data = None
        #self.attributeForm = None
    
    def connect_qgis_signals(self):
        iface = self.iface
        signals = [
            iface.actionAddFeature().toggled,
            iface.layerTreeView().clicked,
            core.QgsProject.instance().legendLayersAdded,
            iface.actionToggleEditing().triggered
        ] 
        for s in signals:
            try:
                s.disconnect(self.disconnect_layer)
            except:
                pass
            s.connect(self.disconnect_layer)
        
    def disconnect_layer(self):
        current_layer = self.iface.activeLayer()
        if current_layer and (current_layer.type() == core.QgsMapLayer.VectorLayer):
            self.activate_qgis_form(current_layer)
            try:
                current_layer.featureAdded.disconnect(self.edit_feature)
            except:
                pass

    def get_layers_to_reclassify(self):
        layers_selected = {}
        currentLayer = self.current_button_layer
        current_uri = currentLayer.dataProvider().uri()
        mapCanvas = self.iface.mapCanvas()
        for lyr in mapCanvas.layers():
            lyr_uri = lyr.dataProvider().uri()
            validate_layer = (
                lyr and 
                (lyr.type() == core.QgsMapLayer.VectorLayer) and 
                (lyr.selectedFeatureCount() > 0) and
                (lyr.geometryType() == currentLayer.geometryType()) and
                (current_uri.database() == lyr_uri.database()) and
                (current_uri.host() == lyr_uri.host()) and
                (current_uri.port() == lyr_uri.port())
            )
            if validate_layer:
                lyrName = lyr.name()
                selectedIds = lyr.selectedFeatureIds()
                layers_selected[lyrName] = [selectedIds, lyr]
        return layers_selected
     
    def run(self, layer_vector, button_data):
        self.connect_qgis_signals()
        self.current_button_layer = layer_vector
        self.iface.setActiveLayer(self.current_button_layer)
        self.current_button_layer.startEditing()
        self.iface.actionAddFeature().trigger() 
        reclassify = button_data['reclassify']  
        if reclassify:
            layers_selected = self.get_layers_to_reclassify()
            if layers_selected:
                self.reclassify_form.emit(
                    button_data['button_data'],
                    layers_selected
                )
        self.current_button_data =  button_data['button_data']
        self.add_feature()

    def add_feature(self):
        button_data = self.current_button_data
        self.set_acquisition_tool(
            button_data['formValues'][u'Escolha ferramenta de aquisição:']
        )
        self.deactivate_qgis_form(self.current_button_layer)
        close_form = button_data['formValues'][u'Fechar form na aquisição:']
        if close_form.lower() == u'sim':
            self.with_form = False
        else:
            self.with_form = True
        self.current_button_layer.featureAdded.connect(
            self.edit_feature
        )

    def deactivate_qgis_form(self, layer_vector):
        setup = layer_vector.editFormConfig()
        setup.setSuppress(QgsEditFormConfig.SuppressOn)
        layer_vector.setEditFormConfig(setup)
    
    def activate_qgis_form(self, layer_vector):
        setup = layer_vector.editFormConfig()
        setup.setSuppress(QgsEditFormConfig.SuppressOff)
        layer_vector.setEditFormConfig(setup)

    def set_attribute_feature(self, lyr, feat):
        button_data = self.current_button_data
        fields = button_data['formValues']
        for field in fields:
            indx = lyr.fields().indexFromName(unicode(field))
            if indx >0:
                config = lyr.editorWidgetSetup(indx).config()
                is_map_value = ('map' in config)
                if is_map_value:
                    valueMap = config['map']
                    if fields[field] in valueMap:
                        feat.setAttribute(indx, valueMap[fields[field]])
                elif fields[field] and not(fields[field] in ['NULL', 'IGNORAR']):
                    value  = fields[field]
                    if re.match('^\@value\(".+"\)$', value):
                        variable = value.split('"')[-2]
                        value = ProjectQgis(self.iface).getVariableProject(variable)
                    feat.setAttribute(indx, value)       

    def open_form(self, fid, lyr, feat):
        self.set_attribute_feature(lyr, feat)
        result = self.iface.openFeatureForm(lyr, feat)
        return result

    def edit_feature(self, fid):
        if fid < 0 and fid != self.fid_before and not(self.ignore):
            self.fid_before = fid
            lyr = self.current_button_layer
            feat = lyr.getFeature(fid)
            lyr.deleteFeature(fid)
            sucess = False
            if self.with_form:
                sucess = self.open_form(fid, lyr, feat)
            else:
                self.set_attribute_feature(lyr, feat)
                sucess = True
            if sucess:
                self.ignore = True
                lyr.addFeature(feat)
                self.ignore = False
     
    def reclassify(self, formValues, layers_selected):
        self.current_button_data = {'formValues' : formValues}
        self.disconnect_layer()
        current_layer =  self.current_button_layer
        current_layer.featureAdded.connect(self.edit_feature)
        self.deactivate_qgis_form(current_layer)
        iface = self.iface
        for lyr_name in layers_selected:
            if formValues[u'{0}_cbx'.format(lyr_name)]:
                layer_origin = layers_selected[lyr_name][1]
                if layer_origin:
                    ids = layers_selected[lyr_name][0]
                    iface.setActiveLayer(layer_origin)
                    current_layer_name = current_layer.dataProvider().uri().table()
                    if lyr_name == current_layer_name:
                        feats = current_layer.getFeatures(ids)
                        for feat in feats:
                            self.set_attribute_feature(current_layer, feat)
                            current_layer.updateFeature(feat)
                    else:
                        layer_origin.removeSelection()
                        layer_origin.selectByIds(ids)
                        self.with_form = False
                        iface.actionCutFeatures().trigger()
                        iface.setActiveLayer(current_layer)
                        iface.actionPasteFeatures().trigger()
        try:
            current_layer.featureAdded.disconnect(self.edit_feature)
        except:
            pass
        iface.activeLayer().removeSelection()

    def set_acquisition_tool(self, tool_name):
        if  tool_name == u'Mão livre':
            self.active_tool([
                u'DSGTools: Ferramenta de Aquisição à Mão Livre',
                u'DSGTools: Free Hand Acquisition'
            ])
        elif tool_name == u'Angulor reto':  
            self.active_tool([
                u'DSGTools: Ferramenta de Aquisição com Ângulos Retos',
                u'DSGTools: Right Degree Angle Digitizing'
            ])  
    
    def active_tool(self, toolName):
        for a in self.iface.mainWindow().findChildren(QtWidgets.QToolBar):
            if a.objectName() == u'DsgTools':
                for action in a.actions():
                    if action.text() in toolName:
                        action.trigger() 
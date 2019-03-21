<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyLocal="1" labelsEnabled="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" readOnly="0" styleCategories="AllStyleCategories" version="3.4.4-Madeira" simplifyMaxScale="1" simplifyDrawingTol="1" simplifyDrawingHints="0" maxScale="0" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 enableorderby="0" type="invertedPolygonRenderer" preprocessing="0" forceraster="0">
    <renderer-v2 enableorderby="0" type="RuleRenderer" forceraster="0" symbollevels="0">
      <rules key="{ef58ec66-1ad3-4f2f-9b8c-9aca93d8934e}">
        <rule key="{ba5a0551-ffb3-449a-ac14-c882b130e34e}" symbol="0"/>
        <rule key="{87742c1f-7b57-426f-9559-642b2955c7d6}" symbol="1"/>
      </rules>
      <symbols>
        <symbol name="0" type="fill" force_rhr="0" clip_to_extent="1" alpha="1">
          <layer enabled="1" pass="0" class="GeometryGenerator" locked="0">
            <prop k="SymbolType" v="Fill"/>
            <prop k="geometryModifier" v="if(  regexp_match(@project_crs_definition, 'longlat' ) > 0, buffer($geometry, -0.001), buffer($geometry, -100))&#xd;&#xa;&#xd;&#xa;&#xd;&#xa;"/>
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
            <symbol name="@0@0" type="fill" force_rhr="0" clip_to_extent="1" alpha="1">
              <layer enabled="1" pass="0" class="SimpleFill" locked="0">
                <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                <prop k="color" v="255,255,255,255"/>
                <prop k="joinstyle" v="bevel"/>
                <prop k="offset" v="0,0"/>
                <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                <prop k="offset_unit" v="MM"/>
                <prop k="outline_color" v="1,124,255,255"/>
                <prop k="outline_style" v="solid"/>
                <prop k="outline_width" v="0.26"/>
                <prop k="outline_width_unit" v="MM"/>
                <prop k="style" v="solid"/>
                <data_defined_properties>
                  <Option type="Map">
                    <Option name="name" type="QString" value=""/>
                    <Option name="properties"/>
                    <Option name="type" type="QString" value="collection"/>
                  </Option>
                </data_defined_properties>
              </layer>
            </symbol>
          </layer>
        </symbol>
        <symbol name="1" type="fill" force_rhr="0" clip_to_extent="1" alpha="1">
          <layer enabled="1" pass="0" class="SimpleFill" locked="0">
            <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="color" v="214,32,26,0"/>
            <prop k="joinstyle" v="bevel"/>
            <prop k="offset" v="0,0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="outline_color" v="157,0,254,255"/>
            <prop k="outline_style" v="solid"/>
            <prop k="outline_width" v="0.6"/>
            <prop k="outline_width_unit" v="MM"/>
            <prop k="style" v="solid"/>
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </symbols>
    </renderer-v2>
  </renderer-v2>
  <customproperties>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory penWidth="0" minScaleDenominator="0" sizeScale="3x:0,0,0,0,0,0" sizeType="MM" diagramOrientation="Up" maxScaleDenominator="1e+08" width="15" opacity="1" enabled="0" minimumSize="0" backgroundAlpha="255" height="15" penAlpha="255" barWidth="5" backgroundColor="#ffffff" labelPlacementMethod="XHeight" penColor="#000000" rotationOffset="270" scaleDependency="Area" lineSizeScale="3x:0,0,0,0,0,0" scaleBasedVisibility="0" lineSizeType="MM">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute field="" label="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings placement="0" showAll="1" priority="0" zIndex="0" dist="0" linePlacementFlags="2" obstacle="0">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration/>
  <aliases/>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults/>
  <constraints/>
  <constraintExpressions/>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
    <columns>
      <column type="actions" hidden="1" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1">.</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>.</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- código: utf-8 -*-
"""
Formas QGIS podem ter uma função Python que é chamada quando o formulário é
aberto.

Use esta função para adicionar lógica extra para seus formulários.

Digite o nome da função na "função Python Init"
campo.
Um exemplo a seguir:
"""
de qgis.PyQt.QtWidgets importar QWidget

def my_form_open(diálogo, camada, feição):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable/>
  <labelOnTop/>
  <widgets/>
  <previewExpression></previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>

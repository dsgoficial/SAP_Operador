from qgis.utils import plugins
import json

class CustomFeatureTool:
    
    def __init__(self, controller):
        self.controller = controller
        self.checkInstallation()
        
    def checkInstallation(self):
        if not( 'DsgTools' in plugins ):
            raise Exception('DsgTools não está instalado!')
        try:
            self.getToolBoxesGuiManager()
            self.getTool()
        except:
            raise Exception('Ferramenta "CustomFeatureTool" não encontrada!')

    def getToolBoxesGuiManager(self):
        return plugins['DsgTools'].guiManager.productionToolsGuiManager.toolBoxesGuiManager

    def getTool(self):
        return plugins['DsgTools'].guiManager.productionToolsGuiManager.toolBoxesGuiManager.cfToolbox

    def run(self, menu):
        from DsgTools.gui.ProductionTools.Toolboxes.CustomFeatureToolBox.customButtonSetup import CustomButtonSetup
        
        self.getToolBoxesGuiManager().showCustomFeatureToolbox()
        
        customFeatureTool = self.getTool()

        setup = json.loads( menu )
        s = CustomButtonSetup()
        s.setName(setup['state']['name'])
        s.setDescription(setup['state']['description'])
        for properties in sorted(
                setup['state']['buttons'], 
                key=lambda data, order=setup['order']: order[ data['name' ] ]
            ):
            properties['color'] = tuple( properties['color'] )
            properties['keywords'] = set( properties['keywords'] )
            s.addButton(properties)
        s.setDynamicShortcut(setup['state']['dynamicShortcut']) 
        customFeatureTool.hideToolEditButton( True )      
        customFeatureTool._order[s.name()] = setup['order']
        customFeatureTool.addButtonSetup(s)
        customFeatureTool.slider.setValue( 16 )

        
from SAP_Operador.modules.qgis.layerActions.flashFeature import FlashFeature

class LayerActionsFactory:

    def __init__(self):
        self.actions = {
            'FlashFeature': FlashFeature()
        }

    def createAction(self, actionName):
        return self.actions[actionName]
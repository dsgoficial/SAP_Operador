
import os
import json

from SAP_Operador.modules.utils.factories.utilsFactory import UtilsFactory
from SAP_Operador.factories.GUIFactory import GUIFactory
from SAP_Operador.factories.spatialVerificationFactory import SpatialVerificationFactory
from SAP_Operador.widgets.pomodoro import Pomodoro
from SAP_Operador.monitoring.canvas import Canvas

from qgis.PyQt import QtCore, QtWidgets, sip
from qgis import core, gui, utils


class ProdToolsCtrl(QtCore.QObject):

    iconRootPath = os.path.join(
        os.path.dirname(__file__),
        '..',
        'icons'
    )

    def __init__(
            self,
            sap=None,
            qgis=None,
            databaseFactory=None,
            processingFactoryDsgTools=None,
            fme=None,
            prodToolsSettings=None,
            toolFactoryDsgTools=None,
            pomodoro=None,
            guiFactory=None,
            spatialVerificationFactory=None,
            canvasMonitoring=None,
            messageFactory=None,
        ):
        super(ProdToolsCtrl, self).__init__()
        self.messageFactory = UtilsFactory().createMessageFactory() if messageFactory is None else messageFactory
        if sap is None:
            return
        self.sap = sap
        self.qgis = qgis
        self.fme = fme
        self.pomodoro = Pomodoro() if pomodoro is None else pomodoro
        self.canvasMonitoring = Canvas() if canvasMonitoring is None else canvasMonitoring
        self.canvasMonitoring.changeStatus.connect(self.pomodoro.setWorkStatusText)
        self.databaseFactory = databaseFactory
        self.processingFactoryDsgTools = processingFactoryDsgTools
        self.guiFactory = GUIFactory() if guiFactory is None else guiFactory
        self.spatialVerificationFactory = SpatialVerificationFactory() if spatialVerificationFactory is None else spatialVerificationFactory
        self.prodToolsSettings = prodToolsSettings
        self.toolFactoryDsgTools = toolFactoryDsgTools
        self.sapActivity = None
        self.productionTools = None
        self.changeStyleWidget = None
        self.nextStyleAction = None
        self.prevStyleAction = None
        self.qgis.on('ReadProject', self.readProjectCallback)
        self.qgis.on('NewProject', self.createProjectCallback)
        self.loadedLayerIds = []
        self.acquisitionMenu = None
        self.validateUserOperations = self.spatialVerificationFactory.createVerification(
            'ValidateUserOperations',
            self.qgis
        )

    def loadChangeStyleWidget(self):
        self.changeStyleWidget = self.guiFactory.getWidget('ChangeStyleWidget', controller=self)
        self.qgis.addWidgetToolBar(self.changeStyleWidget)
        self.changeStyleWidget.setEnabled(False)
        if not self.nextStyleAction:
            self.nextStyleAction = self.qgis.createAction(
                'Próximo estilo',
                os.path.join(self.iconRootPath, 'nextStyle.png'),
                lambda:''
            )
            self.changeStyleWidget.setNextAction(self.nextStyleAction)
            self.prodToolsSettings.addActionMenu(self.nextStyleAction)
        if not self.prevStyleAction:
            self.prevStyleAction = self.qgis.createAction(
                'Último estilo',
                os.path.join(self.iconRootPath, 'prevStyle.png'),
                lambda:''
            )
            self.changeStyleWidget.setPrevAction(self.prevStyleAction)
            self.prodToolsSettings.addActionMenu(self.prevStyleAction)
        return self.changeStyleWidget

    def closedDock(self):
        if self.changeStyleWidget and not sip.isdeleted(self.changeStyleWidget):
            self.changeStyleWidget.clearStyles()
            self.changeStyleWidget.setEnabled(False)
        if self.productionTools:
            self.productionTools.close()

    def getPomodoroWidget(self):
        return self.pomodoro

    def unload(self):
        self.removeDock()
        self.qgis.off('ReadProject', self.readProjectCallback)
        self.qgis.off('NewProject', self.createProjectCallback)

    def loadShortcuts(self):
        shortcuts = self.sapActivity.getShortcuts()
        for shortcut in shortcuts:
            self.qgis.cleanDuplicateShortcut(shortcut['ferramenta'], shortcut['atalho'] if shortcut['atalho'] else '')
        for shortcut in shortcuts:
            self.qgis.setActionShortcut(shortcut['ferramenta'], shortcut['atalho'] if shortcut['atalho'] else '')

    def loadChangeStyleTool(self, stylesName):
        self.changeStyleWidget.setEnabled(True)
        self.changeStyleWidget.clearStyles()
        if not stylesName:
            return
        self.changeStyleWidget.loadStyles(stylesName, stylesName[0])

    def changeMapLayerStyle(self, styleName):
        self.qgis.changeMapLayerStyles(styleName)

    def removeDock(self):
        if self.productionTools:
            self.qgis.removeDockWidget(self.productionTools)

    def getShortcutQgisDescription(self):
        return self.sapActivity.getShortcutsDescription()

    def getActivityDescription(self):
        return self.sapActivity.getDescription()

    def getActivityLineage(self):
        return self.sapActivity.getLineage()

    def getActivityNotes(self):
        return self.sapActivity.getNotes()

    def getActivityRequirements(self):
        return self.sapActivity.getRequirements()

    def getActivityEPSG(self):
        return self.sapActivity.getEPSG()

    def getProject(self):
        return self.sapActivity.getProject()

    def getLot(self):
        return self.sapActivity.getLot()

    def getBlock(self):
        return self.sapActivity.getBlock()

    def getProductType(self):
        return self.sapActivity.getProductType()

    def getScale(self):
        return self.sapActivity.getScale()

    def getUserName(self):
        return self.sapActivity.getUserName()

    def getActivityStyles(self):
        return self.sapActivity.getStylesName()

    def showReportErrorDialog(self):
        self.sap.showReportErrorDialog(
            self.resetProject
        )

    def resetProject(self):
        self.qgis.cleanProject()
        self.reload()

    def getActivityDatabase(self):
        return self.databaseFactory.createPostgres(
            self.sapActivity.getDatabaseName(),
            self.sapActivity.getDatabaseServer(),
            self.sapActivity.getDatabasePort(),
            self.sapActivity.getDatabaseUserName(),
            self.sapActivity.getDatabasePassword()
        )

    def getActivityLayerNames(self):
        return [item["nome"] for item in self.sapActivity.getLayers()]

    def getActivityInputs(self):
        return self.sapActivity.getInputs()

    def frameLoaded(self, frameQuery):
        layers = self.qgis.getLoadedVectorLayers()
        for l in layers:
            if not( l.source() == frameQuery ):
                continue
            return True
        return False

    def setLoadedLayerIds(self, loadedLayerIds):
        self.loadedLayerIds = loadedLayerIds

    def getLoadedLayerIds(self):
        return self.loadedLayerIds

    def getPathDest(self):
        return QtWidgets.QFileDialog.getExistingDirectory(
            self.productionTools if self.productionTools else utils.iface.mainWindow(),
            u"Selecione pasta de destino dos insumos:",
            options=QtWidgets.QFileDialog.Option.ShowDirsOnly
        )

    def loadActivityInputs(self, inputData):
        results = []
        if not inputData:
            self.showInfoMessageBox(None, 'Aviso', 'Selecione o(s) insumo(s)!')
            return

        pathDest = None
        needPath = next((item for item in inputData if item["tipo_insumo_id"] == 1), None)
        if needPath:
            pathDest = self.getPathDest()
        for data in inputData:
            if data['tipo_insumo_id'] in [1]:
                if not pathDest:
                    continue
                data['caminho_padrao'] = pathDest
            result = self.qgis.loadInputData(data)
            results.append(result)
        return results

    def getActivityRoutines(self):
        fmeData = []
        #try:
        fmeData = self.fme.getSapRoutines(self.sapActivity.getFmeConfig())
        #except Exception as e:
        #    self.showErrorMessageBox(None, 'Erro', 'Sem conexão com o FME!')
        return self.sapActivity.getQgisModels() + self.sapActivity.getRuleRoutines() + fmeData

    def runRoutine(self, routineData):
        if not routineData:
            self.showInfoMessageBox(None, 'Aviso', 'Selecione uma rotina!')
            return
        if self.qgis.hasModifiedLayers():
            self.showHtmlMessageDialog(
                self.qgis.getMainWindow(),
                'Aviso',
                '''<p style="color:red">
                    Salve todas suas alterações antes de executar essa rotina!
                </p>'''
            )
            return
        rountineFunctions = {
            'rules': self.runRuleStatistics,
            'fme': self.runFMESAP,
            'qgisModel': self.runQgisModel
        }
        rountineFunctions[routineData['routineType']](routineData)

    def runFMESAP(self, routineData):
        runFMESAP = self.processingFactoryDsgTools.createProcessing('RunFMESAP', self)
        output = runFMESAP.run({
            'workUnitGeometry': self.sapActivity.getWorkUnitGeometry(),
            'fmeRoutine': routineData,
            'dbName': self.sapActivity.getDatabaseName(),
            'dbPort': self.sapActivity.getDatabasePort(),
            'dbHost': self.sapActivity.getDatabaseServer(),
            'dbUser': self.sapActivity.getDatabaseUserName(),
            'dbPassword': self.sapActivity.getDatabasePassword(),
            'sapSubfase': self.sapActivity.getSubphaseId()
        })
        html = "<p>[rotina nome] : {0}</p>".format(routineData['rotina'])
        html += "<p>[status de execução] : {0}</p>".format(output['result']['dados']['status'])
        for flags in output['result']['dados']['sumario']:
            html += """<p>[rotina flags] : {} - {}</p>""".format(flags['classes'], flags['feicoes'])
        self.showHtmlMessageDialog(
            self.qgis.getMainWindow(),
            'Aviso',
            html
        )

    def runRuleStatistics(self, routineData):
        ruleStatistics = self.processingFactoryDsgTools.createProcessing('RuleStatistics', self)
        result = ruleStatistics.run({
            'rules': routineData['ruleStatistics'],
            'layers': self.sapActivity.getLayers()
        })
        self.htmlMessageDlg = self.messageFactory.createMessage('RuleMessageDialog')
        self.htmlMessageDlg.show(
            self.qgis.getMainWindow(),
            'Aviso',
            result,
            self.qgis
        )
        return result

    def runQgisModel(self, routineData):
        html = self.qgis.runProcessingModel(routineData)
        QtWidgets.QApplication.restoreOverrideCursor()
        self.showHtmlMessageDialog(
            self.qgis.getMainWindow(),
            'Aviso',
            html
        )

    def showActivityDataSummary(self):
        dialog = self.guiFactory.makeActivitySummaryDialog(
            self,
            self.getActivityLayerNames(),
            self.sapActivity.getConditionalStyleNames()
        )
        dialog.exec()

    def showHtmlMessageDialog(self, parent, title, message):
        self.htmlMessageDlg = self.messageFactory.createMessage('HtmlMessageDialog')
        self.htmlMessageDlg.show(parent, title, message)

    def showInfoMessageBox(self, parent, title, message):
        messageDlg = self.messageFactory.createMessage('InfoMessageBox')
        messageDlg.show(parent, title, message)

    def showErrorMessageBox(self, parent, title, message):
        messageDlg = self.messageFactory.createMessage('ErrorMessageBox')
        messageDlg.show(parent, title, message)

    def zoomToFeature(self, layerId, layerSchema, layerName):
        self.qgis.zoomToFeature(layerId, layerSchema, layerName)

    def getSapMenus(self):
        return self.sapActivity.getMenus()

    def loadMenu(self):
        try:
            if self.acquisitionMenu:
                self.acquisitionMenu.removeMenuDock()
            customFeatureTool = self.toolFactoryDsgTools.getTool('CustomFeatureTool', self)
            self.acquisitionMenu = customFeatureTool.run( self.getSapMenus() )
        except Exception as e:
            self.showErrorMessageBox( None, 'Erro', str(e) )

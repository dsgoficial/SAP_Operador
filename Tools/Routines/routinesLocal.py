#! -*- coding: utf-8 -*-
from qgis import core, gui
from PyQt5 import QtCore
import re, sys, os, json
from Ferramentas_Producao.Database.postgresql import Postgresql
from Ferramentas_Producao.SAP.managerSAP import ManagerSAP
from Ferramentas_Producao.utils import msgBox
from Ferramentas_Producao.utils.managerQgis import ManagerQgis
import processing, json, platform
from qgis.PyQt.QtXml import QDomDocument

class RoutinesLocal(QtCore.QObject):

    message = QtCore.pyqtSignal(str)
    show_rules_statistics = QtCore.pyqtSignal(str)

    def __init__(self, iface):
        super(RoutinesLocal, self).__init__()
        self.iface = iface
        self.sap_mode = False
        self.is_running = False

    def init_postgresql(self):
        self.postgresql = Postgresql()
        user = ManagerSAP(self.iface).getDatabaseLogin()
        db_name = ManagerSAP(self.iface).getDatabaseName()
        self.postgresql.current_db_name = db_name
        self.postgresql.set_connections_data({
            'db_name' : db_name,
            'db_host' : ManagerSAP(self.iface).getDatabaseServer(),
            'db_port' : ManagerSAP(self.iface).getDatabasePort(),
            'db_user' : user['login'],
            'db_password' : user['senha']
        })

    
    def get_routines_data(self):
        local_routines_formated = []
        if self.sap_mode:
            if ManagerSAP(self.iface).getQgisModels():
                models_qgis = ManagerSAP(self.iface).getQgisModels()
                for model_data in models_qgis:
                    d = {
                        'ordem' : model_data['ordem'],
                        'description' : model_data['descricao'],
                        'type_routine' : 'qgis_model',
                        'model_xml' : model_data['model_xml']
                    }
                    local_routines_formated.append(d)
            if self.is_active_rules_statistics() and ManagerSAP(self.iface).getRules():
                format_rules_data = {}
                for i, d in enumerate(ManagerSAP(self.iface).getRules()):
                    d['tipo_estilo'] = d['grupo_regra']
                    r, g, b = d['cor_rgb'].split(',')
                    d['corRgb'] = [ int(r), int(g), int(b) ]
                    format_rules_data[i] = d
                d = {
                    'ruleStatistics' : format_rules_data, 
                    'description' : "Estatísticas de regras.",
                    'type_routine' : 'rules'
                }
                local_routines_formated.append(d)
        elif self.is_active_rules_statistics():
            d = {
                'ruleStatistics' : [], 
                'description' : "Estatísticas de regras.",
                'type_routine' : 'rules'
            }
            local_routines_formated.append(d)
        return local_routines_formated

    def is_active_rules_statistics(self):
        for alg in core.QgsApplication.processingRegistry().algorithms():
            if "dsgtools:rulestatistics" == alg.id():
                return True
        return False

    def run_rule_statistics(self, rules_data):
        html = ''
        parameters = self.get_paremeters_rule_statistics(rules_data)
        if not parameters['INPUTLAYERS']:
            html += '''<p style="color:red">
                    Não há camadas carregadas.
                </p>'''
        if not parameters['RULEDATA']:
            html += '''<p style="color:red">
                    Não há regras no banco.
                </p>'''
        if not html:
            proc = processing.run(
                "dsgtools:rulestatistics", 
                parameters
            )
            if 'OUTPUT' in proc and proc['OUTPUT']:
                for line in proc['OUTPUT'].split('\n\n'):
                    if '[regras]' in line.lower():
                        html+='<h3>{0}</h3>'.format(line)
                    elif 'passaram' in line.lower():
                        html += u"<p style=\"color:green\">{0}</p>".format(line)
                    else:
                        html += u"<p style=\"color:red\">{0}</p>".format(line)
                self.show_rules_statistics.emit(html)
                return
            else:
                html = "<p style=\"color:red\">{0}</p>".format('Não há regras para as camadas carregadas!')
        self.message.emit(html)

    def get_paremeters_rule_statistics(self, rules_data):
        parameters = { 
            'INPUTLAYERS' : [], 
            'RULEFILE' : '.json', 
            'RULEDATA' : json.dumps(rules_data) 
        }
        m_qgis = ManagerQgis(self.iface)
        layers = m_qgis.get_loaded_layers()
        for lyr in layers:
            data_provider = lyr.dataProvider().uri()
            if not data_provider.database():
                continue
            layer_uri = lyr.dataProvider().uri().uri()
            parameters['INPUTLAYERS'].append(
                layer_uri if platform.system() == 'Windows' else layer_uri.replace('checkPrimaryKeyUnicity=\'1\' ' , '')
            )
        return parameters

    def run(self, routine_data):
        self.init_postgresql()
        if "ruleStatistics" in routine_data:
            if self.sap_mode:
                self.run_rule_statistics(routine_data['ruleStatistics'])
            else:
                self.run_rule_statistics(self.postgresql.get_rules_data())
        if 'model_xml' in routine_data:
            self.run_processing_model(routine_data['model_xml'])
    
    def run_processing_model(self, model_xml):
        doc = QDomDocument()
        doc.setContent(model_xml)
        model = core.QgsProcessingModelAlgorithm()
        model.loadVariant(core.QgsXmlUtils.readVariant( doc.firstChildElement() ))
        processing.runAndLoadResults(model, {})
        html = "<p style=\"color:red\">{0}</p>".format('Rotina executada!')
        self.message.emit(html)

        
        
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, uic, QtWidgets
import os, sys, platform, pickle, webbrowser
from qgis import core, gui, utils
from Ferramentas_Producao.Tools.LoadData.Views.authSmb import AuthSmb
from Ferramentas_Producao.utils import msgBox
from Ferramentas_Producao.SAP.managerSAP import ManagerSAP

class LoadInputs:
    
    def __init__(self, iface, postgresql, load_layers, parent=None):
        self.iface = iface
        self.postgresql = postgresql
        self.parent = parent
        self.load_layers = load_layers

    def load(self, settings_data):
        sap_data = ManagerSAP(self.iface).load_data()
        files_data = {
            1 : [], #download
            2 : [], #open via net *
            3 : [], #postgis
            4 : [], #text
            5 : [], #url
            6 : [], #wms
            7 : []  #wfs
        }
        for d in sap_data['dados']['atividade']['insumos'] :
            if d['nome'] in settings_data['input_files']:
                files_data[d['tipo_insumo_id']].append({ 
                    'file_name' : d['nome'],
                    'path_origin' : d['caminho'],
                    'epsg' : d['epsg'],
                    'path_dest' : d['caminho_padrao']
                })
        erro = []
        erro += self.load_files(files_data[1])
        self.load_urls(files_data[5])
        erro += self.load_wms(files_data[6])
        erro += self.load_wfs(files_data[7])
        self.load_pg_layers(files_data[3])
        erro += self.load_files(files_data[2])
        self.show_msg(files_data[4], 'message') if len(files_data[4]) > 0 else ''
        self.show_msg(erro) if len(erro) > 0 else ''

    def load_files_from_network(self, files_data):
        erro = []
        os_name = platform.system()
        if os_name == 'Windows': 
            for d in files_data:
                path_file = d['path_origin']
                file_name = d['file_name']
                epsg = d['epsg']
                if not self.add_raster_layer(file_name, path_file, epsg):
                    erro.append(
                        'arquivo: falha ao carregar arquivo "{0}" a partir da rede'.format(path_file)
                    )
        return erro

    def load_files(self, files_data):
        erro = []
        if  files_data:
            files_down_data, erro_downloads = self.download(files_data)
            erro = erro + erro_downloads
            for d in files_down_data:
                path_file = d['path_file']
                file_name = d['file_name']
                epsg = d['epsg']
                if not self.add_raster_layer(file_name, path_file, epsg):
                    erro.append(
                        'raster: falha ao carregar arquivo "{0}" tente carregar manualmente'.format(path_file)
                    )
        return erro
    
    def load_urls(self, files_data):
        for d in files_data:
            self.open_url(d['path_origin'])
    
    def load_wms(self, files_data):
        erro = []
        for d in files_data:
            uri = d['path_origin']
            erro.append('wms: falha ao carregar o seguinte wms "{0}"'.format(uri)) if not self.add_wms_layer( uri, d['nome'] ) else ''
        return erro
    
    def load_wfs(self, files_data):
        erro = []
        for d in files_data:
            uri = d['path_origin']
            erro.append('wfs: falha ao carregar o seguinte wfs "{0}"'.format(uri)) if not self.add_wfs_layer( uri, d['nome'] ) else ''
        return erro

    def load_pg_layers(self, files_data):
        #loadLayers = LoadLayers(self.sap_mode, self.postgresql, self.iface, self.frame)
        for d in files_data:
            self.add_pg_layer(d['path_origin'], d['file_name'], d['epsg'])

    def download(self, files_data):
        erro = []
        files_down_data = []
        ask_path = False
        for d in files_data:
            if not d['path_dest']:
                ask_path = True
                break
        if ask_path:            
            path_dest = self.get_path_dest()
            if not path_dest:
                return files_down_data, erro
        for d in files_data:
            path_origin = d['path_origin']
            path_file = self.download_file(path_origin, d['path_dest'] if d['path_dest'] else path_dest)
            if path_file:
                d['path_file'] = path_file
                files_down_data.append(d)
            else:
                erro.append('download: falha no download do arquivo "{0}"'.format(d['path_origin']))
        return files_down_data, erro

    def get_path_dest(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self.parent if self.parent else utils.iface.mainWindow(), 
            u"Selecione pasta de destino dos insumos:",
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )
        return path

    def make_path_dest(self, path_dest):
        try:
            os.makedirs(path_dest)
        except FileExistsError:
            pass

    def download_file_windows(self, path_origin, path_dest):
        path_origin = path_origin.replace(u"/", u"\\")
        name_file = path_origin.split(u"\\")[-1]
        path_dest = path_dest.replace(u"/", u"\\")
        local_file_path = os.path.join(path_dest, name_file)
        command = u'copy "{0}" "{1}"'.format(
            path_origin,
            path_dest
        )
        self.make_path_dest(path_dest)
        proc = os.popen(command)  
        proc.read()
        proc.close()
        return local_file_path
    
    def download_file_linux(self, path_origin, path_dest):
        aut_smb = self.get_auth_smb()
        if not aut_smb:
            return False
        path_origin = path_origin.replace(u"\\", u"/")
        name_file = path_origin.split(u"/")[-1] 
        local_file_path = os.path.join(path_dest, name_file)
        command = u'{0} {1} {2} "{3}" {4} {5} {6}'.format(
            self.get_python_version(),
            self.get_script_path(),
            "smb:{0}".format(path_origin),
            local_file_path,
            aut_smb.user,
            aut_smb.passwd,
            aut_smb.domain
        )
        self.make_path_dest(path_dest)
        proc = os.popen(command)
        proc.read()
        proc.close()
        return local_file_path

    def download_file(self, path_origin, path_dest):
        try:
            os_name = platform.system()
            if os_name == 'Windows':
                local_file_path = self.download_file_windows(path_origin, path_dest)  
            else:
                local_file_path = self.download_file_linux(path_origin, path_dest)
            if os.path.exists(local_file_path):
                return local_file_path
            return False
        except:
            return False

    def get_auth_smb(self):
        auth_smb = AuthSmb(self.parent if self.parent else utils.iface.mainWindow())
        r = auth_smb.exec_()
        if r:
            return auth_smb
        return False

    def get_python_version(self):
        try:
            import smbc
            return "python3"
        except:
            return "python"

    def get_script_path(self):
        script_path = os.path.join(
            os.path.dirname(__file__),
            "scripts",
            "get_file_smb.py"
        )
        return script_path

    def add_pg_layer(self, db_path, layer_name, epsg):
        uri_text = self.get_uri_text(db_path, epsg)
        v_lyr = core.QgsVectorLayer(uri_text, layer_name, u"postgres")
        vl = core.QgsProject.instance().addMapLayer(v_lyr, False)
        vl.setReadOnly(True)
        layers_data = self.load_layers.get_layers_data([ vl.dataProvider().uri().table() ])
        if layers_data:
            layer_data = layers_data[0]
            self.load_layers.add_layer_values_map(vl, layer_data)
        group_name = 'MOLDURA_E_INSUMOS'
        if self.load_layers.db_group :
            group = self.load_layers.db_group.findGroup(group_name)
        else:
            root = core.QgsProject.instance().layerTreeRoot()
            group = root.findGroup(group_name)
        if not group:
            group = root.addGroup(group_name)
        group.insertLayer(0, vl)
            
    def get_uri_text(self, db_path, epsg):
        sap_data = ManagerSAP(self.iface).load_data()['dados']['atividade']
        db_address, db_name, db_schema, layer_name = db_path.split('/')
        db_host, db_port = db_address.split(':')
        connection_config = self.postgresql.get_connection_config()
        template_uri = u"""dbname='{}' host={} port={} user='{}' password='{}' table="{}"."{}" (geom) sql={}"""
        uri_text = template_uri.format(
            db_name, 
            db_host, 
            db_port, 
            connection_config['db_user'],
            connection_config['db_password'],
            db_schema,
            layer_name,
            u"""ST_INTERSECTS(geom, ST_TRANSFORM(ST_GEOMFROMEWKT('{0}'), {1}))""".format(sap_data['geom'], epsg)
        )
        return uri_text

    def add_raster_layer(self, raster_name, raster_path, epsg):
        s = QtCore.QSettings()
        val_bkp = s.value("Projections/defaultBehavior")
        s.setValue("Projections/defaultBehavior", "useGlobal")
        crs = core.QgsCoordinateReferenceSystem(int(epsg))
        layer = core.QgsRasterLayer(raster_path, raster_name)
        layer.setCrs(crs)
        s.setValue("Projections/defaultBehavior", val_bkp)
        if layer.isValid():
            core.QgsProject.instance().addMapLayer(layer)
            return True
        return False

    def add_wms_layer(self, uri, name):
        layer = core.QgsRasterLayer(uri, name, 'wms')
        if layer.isValid():
            core.QgsProject.instance().addMapLayer(layer)
            return True           

    def add_wfs_layer(self, uri, name):
        layer = core.QgsVectorLayer(uri, name, 'WFS')
        if layer.isValid():
            core.QgsProject.instance().addMapLayer(layer)
            return True

    def open_url(self, url):
        try:
            webbrowser.get('firefox').open(url)
        except:
            webbrowser.open(url)

    def show_msg(self, content, tag='erro'):
        if tag == 'erro':
            html=u"<p>Erros ao carregar insumos:</p>"
            p = u"<p>{0}</p>"
            for e in content:
                html += p.format(e)
            msgBox.show(
                text=html, 
                title=u"Error", 
                status='critical', 
                parent=self.parent if self.parent else utils.iface.mainWindow()
            )
        else:
            html=''
            p = "<p>{0}</p>"
            for e in content:
                html += p.format(e)
            msgBox.show(
                text=html, 
                title='Aviso', 
                parent=self.parent if self.parent else utils.iface.mainWindow()
            )
        
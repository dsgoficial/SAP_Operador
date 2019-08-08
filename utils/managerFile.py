# -*- coding: utf-8 -*-
from PyQt5 import QtCore, uic, QtWidgets
import os, sys, platform, pickle
from qgis import utils
from .authSmb import AuthSmb
from utils import msgBox


def dump_data(path_data, data):
    with open(path_data, u"wb") as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

def load_data(path_data):
    try:
        with open(path_data, u"rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return False

def get_path_dest(parent):
    path = QtWidgets.QFileDialog.getExistingDirectory(
        parent, 
        u"Selecione pasta de destino dos insumos:",
        options=QtWidgets.QFileDialog.ShowDirsOnly
    )
    return path

def get_auth_smb(parent):
    auth_smb = AuthSmb(parent)
    r = auth_smb.exec_()
    if r:
        return auth_smb
    return False

def get_python_version():
    try:
        import smbc
        return "python3"
    except:
        return "python"

def get_script_path():
    script_path = os.path.join(
        os.path.dirname(__file__),
        "scripts",
        "get_file_smb.py"
    )
    return script_path

def download_file(path_origin, path_dest, parent):
    try:
        os_name = platform.system()
        if os_name == 'Windows':
            path_origin = path_origin.replace(u"/", u"\\")
            name_file = path_origin.split(u"\\")[-1]
            path_dest = path_dest.replace(u"/", u"\\")
            local_file_path = os.path.join(path_dest, name_file)
            command = u'copy "{0}" "{1}"'.format(
                path_origin,
                path_dest
            )
            proc = os.popen(command)  
            proc.read()
            proc.close()
        elif os_name == 'Linux':
            aut_smb = get_auth_smb(parent)
            if aut_smb:
                path_origin = path_origin.replace(u"\\", u"/")
                name_file = path_origin.split(u"/")[-1] 
                local_file_path = os.path.join(path_dest, name_file)
                command = u'{0} {1} {2} "{3}" {4} {5} {6}'.format(
                    get_python_version(),
                    get_script_path(),
                    "smb:{0}".format(path_origin),
                    local_file_path,
                    aut_smb.user,
                    aut_smb.passwd,
                    aut_smb.domain
                )
                proc = os.popen(command)
                proc.read()
                proc.close()
            else:
                return False
        if os.path.exists(local_file_path):
            return local_file_path
        return False
    except:
        return False

def download(paths_data, parent=utils.iface.mainWindow()):
    erro = []
    files_data = []
    path_dest = get_path_dest(parent)
    if path_dest == '':
        return files_data
    for f_data in paths_data:
        path_origin = f_data['path_origin']
        path_file = download_file(path_origin, path_dest, parent)
        if path_file:
            files_data.append({
                'path_file' : path_file,
                'epsg' : f_data['epsg'],
                'file_name' : f_data['file_name']
            })
        else:
            erro.append(path_file)
    show_erro(erro, parent) if len(erro) > 0 else ''
    return files_data

def show_erro(erro, parent):
    html=u"<p>Erro em baixar os seguintes arquivos:</p>"
    p = u"<p>{0}</p>"
    for e in erro:
        html += p.format(e)
    msgBox.show(text=html, title=u"Error", status='critical', parent=parent) 
from SAP_Operador.modules.qgis.inputs.inputData import InputData


class UnsupportedPostgis(InputData):
    # Insumo de banco PostGIS (tipo de insumo 3). Até a 4.3.0 ele abria com a
    # credencial do banco de produção da atividade (tipos 2 e 3 de dado de
    # produção). No SAP 3.0 toda produção é base versionada, sem banco e sem
    # credencial a repassar: o insumo é recusado com o motivo, e nada carrega.

    def __init__(self):
        super(UnsupportedPostgis, self).__init__()

    def load(self, fileData):
        self.showErrorMessageBox(
            '<p>O insumo "{0}" é uma camada de banco PostGIS, que o SAP Operador não abre mais: '
            'no SAP 3.0 o plugin não recebe credencial de banco. A camada não foi carregada.</p>'.format(
                fileData.get('nome') or '-'
            )
        )
        return None

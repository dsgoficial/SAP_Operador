import json
from qgis import core

# As colunas ocultas vêm do SAP (atividade.colunas_ocultas), configuradas pelo
# SAP_Gerente por subfase e lote. Cada item traz 'definicao_colunas', um JSON em
# texto no formato {"<tabela>": ["<coluna>", ...]}; a chave "*" vale para toda
# camada da atividade. Este módulo não define nenhuma coluna por conta própria.
#
# Uma coluna oculta some da tabela de atributos E do formulário de edição (widget
# "Hidden"). O operador pode reexibir tudo pelo painel (setVisible); o estado
# original de cada coluna é guardado e restaurado.

LOG_TAG = 'SAP_Operador'
HIDDEN_WIDGET_TYPE = 'Hidden'


def log(message, level=core.Qgis.MessageLevel.Warning):
    core.QgsMessageLog.logMessage(message, LOG_TAG, level)


def parseDefinitions(items):
    """Une as definições recebidas do SAP em {tabela: {colunas em minúsculas}}."""
    merged = {}
    for item in items or []:
        name = item.get('nome', '?') if isinstance(item, dict) else '?'
        try:
            definition = item['definicao_colunas']
            if isinstance(definition, str):
                definition = json.loads(definition)
            if not isinstance(definition, dict):
                raise ValueError('a definição deve ser um objeto JSON')
            for table, columns in definition.items():
                if not isinstance(columns, list):
                    raise ValueError('a tabela {} deve ter uma lista de colunas'.format(table))
                merged.setdefault(str(table), set()).update(
                    str(column).lower() for column in columns
                )
        except (KeyError, TypeError, ValueError) as e:
            log('Colunas ocultas "{}" ignoradas: {}'.format(name, e))
    return merged


def getHiddenColumns(tableName, definitions):
    return definitions.get('*', set()) | definitions.get(tableName, set())


class HiddenColumnsManager:

    def __init__(self):
        self.visible = False
        # layerId -> {fieldName: {'wasHidden': bool, 'widgetSetup': QgsEditorWidgetSetup}}
        self.entries = {}

    def isEmpty(self):
        return not self.entries

    def clear(self):
        """Esquece as camadas e volta ao estado padrão (oculto), para a próxima atividade."""
        self.entries = {}
        self.visible = False

    def getTableName(self, layer):
        try:
            return layer.dataProvider().uri().table() or layer.name()
        except Exception:
            return layer.name()

    def apply(self, layer, definitions):
        """Registra as colunas da camada a ocultar e as oculta, se o estado for oculto.

        Retorna os nomes das colunas registradas. Coluna inexistente na camada é
        ignorada (só aviso informativo no log).
        """
        if not definitions:
            return []
        if layer is None or not layer.isValid():
            log('Camada inválida; colunas não foram ocultadas.')
            return []
        tableName = self.getTableName(layer)
        wanted = getHiddenColumns(tableName, definitions)
        if not wanted:
            return []
        try:
            fields = layer.fields()
            entry = self.entries.setdefault(layer.id(), {})
            tableConfig = layer.attributeTableConfig()
            hiddenNow = {
                column.name: column.hidden
                for column in tableConfig.columns()
                if column.type == core.QgsAttributeTableConfig.Type.Field
            }
            found = set()
            for field in fields:
                if field.name().lower() not in wanted:
                    continue
                found.add(field.name().lower())
                if field.name() in entry:
                    continue
                entry[field.name()] = {
                    'wasHidden': hiddenNow.get(field.name(), False),
                    'widgetSetup': layer.editorWidgetSetup(fields.indexOf(field.name()))
                }
            missing = wanted - found
            if missing:
                log(
                    'Camada {}: colunas não encontradas: {}'.format(
                        tableName, ', '.join(sorted(missing))
                    ),
                    core.Qgis.MessageLevel.Info
                )
            if not entry:
                del self.entries[layer.id()]
                return []
            if not self.visible:
                self.enforce(layer, hide=True)
            return list(entry.keys())
        except Exception as e:
            log('Falha ao ocultar colunas da camada {}: {}'.format(tableName, e))
            return []

    def enforce(self, layer, hide):
        """Aplica o estado oculto (hide=True) ou restaura o original (hide=False)."""
        entry = self.entries.get(layer.id())
        if not entry:
            return
        fields = layer.fields()
        tableConfig = layer.attributeTableConfig()
        columns = tableConfig.columns()
        for column in columns:
            if column.type != core.QgsAttributeTableConfig.Type.Field:
                continue
            if column.name in entry:
                column.hidden = True if hide else entry[column.name]['wasHidden']
        tableConfig.setColumns(columns)
        layer.setAttributeTableConfig(tableConfig)
        for name, state in entry.items():
            index = fields.indexOf(name)
            if index < 0:
                continue
            layer.setEditorWidgetSetup(
                index,
                core.QgsEditorWidgetSetup(HIDDEN_WIDGET_TYPE, {}) if hide else state['widgetSetup']
            )

    def getLayers(self):
        project = core.QgsProject.instance()
        layers = []
        for layerId in list(self.entries.keys()):
            layer = project.mapLayer(layerId)
            if layer is None:
                del self.entries[layerId]
                continue
            layers.append(layer)
        return layers

    def setVisible(self, visible):
        """visible=True reexibe as colunas (tabela e formulário); False volta a ocultá-las."""
        self.visible = bool(visible)
        for layer in self.getLayers():
            try:
                self.enforce(layer, hide=not self.visible)
            except Exception as e:
                log('Falha ao atualizar colunas da camada {}: {}'.format(layer.name(), e))

    def refresh(self):
        """Reaplica o estado atual (ex.: após a troca de estilo, que pode restaurar o formulário)."""
        self.setVisible(self.visible)

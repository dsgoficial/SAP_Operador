# No SAP 3.0 toda produção é BASE VERSIONADA (tipo 4 de
# dominio.tipo_dado_producao), decisão de 2026-10-15: o plugin atende só ela.
# Os tipos 1, 2 e 3 (dado fora do SAP e banco PostGIS) deixaram de existir, e o
# pacote de um servidor antigo que ainda os mande é recusado com o motivo.
VERSIONED_BASE = 4

PRODUCTION_DATA_NAMES = {
    1: 'dado não controlado pelo SAP',
    2: 'banco PostGIS com controle de permissões',
    3: 'banco PostGIS',
}


def getProductionDataType(package):
    """O tipo de dado de produção do pacote, ou None quando ele não vem.

    O servidor 3.38.0 ainda manda `dado_producao.tipo_dado_producao_id` = 4 por
    uma versão e depois deixa de mandar: a ausência não é motivo de recusa.
    """
    activity = ((package or {}).get('dados') or {}).get('atividade') or {}
    productionData = activity.get('dado_producao') or {}
    value = productionData.get('tipo_dado_producao_id')
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def getUnsupportedReason(package, versioning):
    """O motivo de recusar o pacote, ou None quando ele é da base versionada.

    `versioning` é a seção `versionamento` que o modelo da atividade já leu
    (None quando o pacote não a traz com `repo_id`).
    """
    productionType = getProductionDataType(package)
    if productionType is not None and productionType != VERSIONED_BASE:
        name = PRODUCTION_DATA_NAMES.get(productionType)
        return (
            'Esta atividade é de dado de produção do tipo {0}{1}, que o SAP Operador não atende mais: '
            'no SAP 3.0 toda produção é base versionada (tipo 4). Atualize o servidor do SAP ou peça '
            'ao gerente que configure a subfase com base versionada.'
        ).format(productionType, ' ({0})'.format(name) if name else '')
    if versioning is None:
        return (
            'O SAP não enviou a base versionada desta atividade (seção "versionamento" com o repositório), '
            'e o SAP Operador só atende a base versionada. Atualize o servidor do SAP ou peça ao gerente '
            'que confira a configuração da subfase.'
        )
    return None

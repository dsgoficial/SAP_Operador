# SAP Operador

Plugin QGIS 4.x para gerenciamento de produção cartográfica da DSG (Diretoria do Serviço Geográfico do Exército Brasileiro).

## Stack

- **QGIS 4.0+** com PyQt6
- **Python 3.9+**
- **PostgreSQL/PostGIS** via `psycopg2`
- **HTTP/REST** via `requests`
- Integração opcional: DSGTools, FME

## Estrutura do Projeto

```
main.py                  # Entry point do plugin
config.py                # NAME e VERSION
metadata.txt             # Metadados do plugin QGIS
controllers/             # Controllers (MVC) - lógica de negócio
  remoteProdToolsDockCtrl.py  # Atividades remotas (SAP HTTP)
  localProdToolsDockCtrl.py   # Atividades locais (PostgreSQL)
  loginCtrl.py                # Autenticação
  prodToolsSettingsCtrl.py    # Configurações e menu
factories/               # Factories, Singletons e Builders
interfaces/              # Interfaces abstratas (prefixo I*)
modules/                 # Módulos de funcionalidade
  sap/                   # Integração com SAP (api, controllers, dataModels)
  qgis/                  # Abstração da API QGIS (qgisApi.py)
  dsgTools/              # Integração DSGTools (processing launchers)
  database/              # Conectividade PostgreSQL/PostGIS
  fme/                   # Integração FME via HTTP
  utils/                 # Utilitários e mensagens
  pomodoro/              # Timer de produtividade
  pluginUpdater/         # Auto-atualização do plugin
widgets/                 # Componentes de UI
uis/                     # Arquivos .ui (Qt Designer)
icons/                   # Ícones e imagens
```

## Arquitetura e Padrões

- **MVC**: Controllers (`*Ctrl.py`) orquestram lógica; widgets são views; dataModels são models
- **Factory Pattern**: `GUIFactory`, `DatabaseFactory`, `DataModelFactory`, etc.
- **Singleton**: `LoginSingleton`, `SapApiHttpSingleton`, `ChangeStylesSingleton`
- **Builder**: `ProductionToolsBuilder/Director`, `ActivityWidgetDirector`
- **Interfaces**: Classes abstratas com prefixo `I` (ex: `IQgisApi`, `ISapApi`)
- **Dependency Injection**: Controllers recebem dependências no construtor

## Convenções

- **Idioma do código**: nomes de classes, métodos e variáveis em inglês; comentários e mensagens ao usuário em português
- **Controllers**: sufixo `Ctrl` (ex: `LoginCtrl`, `RemoteSapCtrl`)
- **Interfaces**: prefixo `I` (ex: `IQgisApi`)
- **Factories**: sufixo `Factory` ou `Singleton`
- **Métodos privados**: prefixo `_` (ex: `_privateMethod`)
- **camelCase** para métodos e variáveis
- **PascalCase** para classes
- **Versionamento**: manter `config.py` e `metadata.txt` sincronizados

## Desenvolvimento

### Setup local

Usar scripts em `.dev/` para criar symlink do repositório para o diretório de plugins do QGIS:
- Windows: `.dev/setup_dev_windows.bat` (requer admin)
- Linux: `.dev/setup_dev_linux.sh`
- macOS: `.dev/setup_dev_macos.sh`

### Branch atual

- `qgis4` — migração para QGIS 4 / PyQt6
- `master` — branch principal

### Testes

Sem framework de testes automatizados. Testes são manuais dentro do QGIS.

## Comandos úteis

```bash
# Ver diff das mudanças
git diff

# Verificar status
git status
```

## Notas importantes

- Ao modificar APIs do QGIS, verificar compatibilidade com QGIS 4.x (PyQt6, enums com escopo completo)
- O plugin se auto-atualiza via `modules/pluginUpdater/`
- Validação de regras é ignorada em etapas de revisão (commit 9a478d2)

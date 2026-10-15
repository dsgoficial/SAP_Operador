# SAP Operador

Plugin QGIS 4.x para gerenciamento de produção cartográfica da DSG (Diretoria do Serviço Geográfico do Exército Brasileiro).

## Stack

- **QGIS 4.0+** com PyQt6
- **Python 3.9+**
- **PostgreSQL** via `psycopg2`, só no modo local (o pacote em `public.sap_local` do banco local do login)
- **HTTP/REST** via `requests`
- Integração opcional: DSGTools (o FME saiu na 4.3.0)

## Estrutura do Projeto

```
main.py                  # Entry point do plugin
config.py                # NAME e VERSION
metadata.txt             # Metadados do plugin QGIS
controllers/             # Controllers (MVC) - lógica de negócio
  remoteProdToolsDockCtrl.py  # Atividades remotas (SAP HTTP)
  localProdToolsDockCtrl.py   # Atividades locais (pacote em public.sap_local, camadas do GeoPackage de campo)
  loginCtrl.py                # Autenticação
  prodToolsSettingsCtrl.py    # Configurações e menu
factories/               # Factories, Singletons e Builders
interfaces/              # Interfaces abstratas (prefixo I*)
modules/                 # Módulos de funcionalidade
  sap/                   # Integração com SAP (api, controllers, dataModels)
  qgis/                  # Abstração da API QGIS (qgisApi.py)
  dsgTools/              # Integração DSGTools (processing launchers)
  versionamento/         # Provedor dsgversioning, GeoPackage de campo, painel e conflitos
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

- `sap3`: versão 4.x, fala SÓ com o servidor SAP 3.0, só QGIS 4
- `qgis4`: versão 3.x, migração para QGIS 4 / PyQt6, servidor SAP 2.3.x
- `master`: branch principal

### Contrato com o servidor (branch `sap3`)

- O servidor é o SAP 3.0 (repositório `controle_acervo`), e ele é a fonte da verdade do contrato: rotas em `server/src/{login,distribuicao,metadado,microcontrole}/*_route.js`, corpos nos `*_schema.js` (Joi) e o pacote da atividade em `distribuicao_ctrl.js` (`getDadosAtividade`).
- Só a BASE VERSIONADA (tipo 4 de `dominio.tipo_dado_producao`, decisão de 2026-10-15): o pacote de outro tipo, ou sem a seção `versionamento`, é recusado com o motivo (`modules/sap/dataModels/productionData.py`). O plugin não depende de `tipo_dado_producao_id`, `login_info` nem `configuracao_producao`; o PostGIS de produção saiu na 4.4.0.
- O plugin e o servidor sobem em LOCKSTEP, sem compatibilidade com o SAP 2.3.x. `validVersion` (`modules/sap/api/sapHttp.py`) aceita só major `3`, e o servidor barra no login do cliente `sap_fp` o plugin abaixo da versão mínima de `qgis.plugin`.
- Chave desconhecida no corpo: `microcontrole` e `metadados` recusam com 400; `distribuicao` e `login` descartam a chave e avisam em `avisos`. Nos dois casos o campo não chega ao banco, então nome de campo se copia do schema, nunca da memória.
- Nomes do 3.0 que o plugin usa: `versao_id` e `uuid_versao` no metadado de edição (o que se publica é a EDIÇÃO, `acervo.versao`), `usuario_uuid`, `subtipo_produto`, `atalhos`. `denominador_escala` é derivado das folhas da unidade de trabalho e vem null quando elas têm escalas diferentes ou nenhuma: o plugin tolera o null.
- Token vencido é 401 (o plugin refaz o login); 403 é falta de perfil de operador no módulo de produção.

### Testes

Testes automatizados no QGIS 4 real, sem interface, em `tests/versionamento/`: `prova_qgis.py` (cenários `versionado` e `recusa`) e `prova_campo.py` (`campo` e `recusa`), rodados por `python-qgis.bat` com `QT_QPA_PLATFORM=offscreen` e `DSGTOOLS_PATH`; o uso está no cabeçalho de cada um. O resto do plugin ainda se testa à mão dentro do QGIS.

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

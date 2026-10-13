# CHANGELOG

## 4.0.0

4.0.0: contrato do SAP 3.0, só QGIS 4.

Requisito:
- Servidor SAP 3.x. O plugin recusa servidor 2.x no login ("Versão do servidor SAP incompatível"), e o SAP 3.0 recusa plugin antigo: os dois sobem juntos, sem compatibilidade com o SAP 2.3.x.
- Perfil de operador no módulo de produção do SAP 3.0. Sem ele o servidor responde 403, e o plugin mostra a mensagem do servidor.

Mudanças de contrato:
- Metadado de edição por EDIÇÃO, e não por folha: a tela "Editar metadados" grava por `versao_id` (era `produto_id`), e "Baixar JSON" pede `/metadados/json_edicao/produto/{uuid}` com o `uuid_versao` (era `produto_uuid`, que o SAP 3.0 não manda, e todas as folhas saíam "sem uuid, ignorado"). A lista mostra a versão ao lado da folha, e o arquivo baixado leva a versão no nome.
- Escala: no SAP 3.0 a escala é da folha, e o servidor manda `denominador_escala` derivado das folhas ligadas à unidade de trabalho, ou null quando elas têm escalas diferentes ou nenhuma. Com escala, o painel, as variáveis de projeto `escala` e `productiontools_scale` e a grade de revisão funcionam como antes. Com null, o painel mostra "Escala: -", as variáveis não são definidas (antes o carregamento de camadas falhava ao converter "-" em número) e a grade de revisão usa a das escalas menores que 1:10.000.
- Tipo de produto lido de `subtipo_produto` (era `tipo_produto`), que no SAP 3.0 vem da linha de produção.
- Usuário da atividade lido de `usuario_uuid` (era `usuario_id`).
- Acesso ao banco de produção (dado PostGIS com controle de permissão): quando o SAP 3.0 não consegue conceder o acesso, `login_info` chega como `{erro}`, e o plugin mostra essa frase em vez de falhar com KeyError. Sem `login_info`, avisa que o SAP não enviou o acesso.
- Rotinas FME: o gerenciador vem como `url` (era `servidor` e `porta`, que o SAP já não mandava).
- Sessão: o token vencido responde 401 no SAP 3.0, e é no 401 que o plugin refaz o login sozinho. O 403 (falta de perfil) e o 404 (atividade ou versão não encontrada) mostram a mensagem do servidor, em vez de "Token expirado" e "Servidor não encontrado".

## 3.31.0

Melhorias:
- Colunas ocultas por atividade. O SAP passa a enviar, na atividade, a lista de colunas que o projeto oculta por subfase e lote (configurada no SAP_Gerente). Ao carregar as camadas, o operador oculta essas colunas na tabela de atributos e no formulário de edição; nada é definido no plugin. Colunas que não existem na camada são ignoradas e registradas no painel de mensagens do QGIS, aba "SAP_Operador".
- Nova caixa "Exibir colunas ocultas" no painel do plugin (aparece só quando a atividade tem configuração). Marcada, reexibe as colunas na tabela e no formulário, com o estado original (inclusive listas de valores); desmarcada, volta a ocultá-las. Começa desmarcada a cada atividade.
- A troca de estilo do mapa reaplica o estado das colunas ocultas, pois o QGIS restaura o formulário salvo no estilo.

Requisito:
- Servidor SAP 2.3.6 ou superior. Em servidores anteriores o plugin funciona normalmente, sem colunas ocultas.

## 3.30.2

Correção de bug:
- Rotinas de modelo QGIS não falham mais com "TypeError: checkParameterValues(): argument 1 has unexpected type 'int'" quando o campo "parametros" do perfil de modelo é um valor JSON escalar (por exemplo "1"). Parâmetros vazios ou nulos são tratados como {}; JSON malformado ou que não seja um objeto exibe mensagem de erro clara.

## 3.30.1

Melhorias:
- O atualizador de plugins passa a consultar o metadata.txt de cada plugin do repositório de rede e ignora os que não declaram suporte à versão do QGIS em execução (qgisMinimumVersion/qgisMaximumVersion; sem máximo declarado, vale "<major do mínimo>.99"). Assim, builds para QGIS 3 não são mais instalados nem sobrescrevem plugins no QGIS 4. Cada plugin ignorado é registrado no painel de mensagens do QGIS, aba "SAP Operador".
- Remoção da ferramenta "Fechar linha", já incorporada ao DSGTools.
- Remoção de código sem uso: ferramentas "Aparar linha" e "Expandir linha", paginação de rasters (grupo "imagens_dinamicas"), ação vazia "Atualizador de plugins local" do menu e "Reclassify Mode" (desativado desde a 3.29.16; o atalho equivalente do DSGTools continua disponível).

Correção de bug:
- Versão exibida na tela de login sincronizada com o metadata.txt.

## 3.30.0

Melhorias:
- Captura de microcontrole da produção. Quando a subfase está configurada para monitoramento por feição, o operador acumula por camada as operações de inserção, remoção, atualização de atributo e atualização de geometria (com comprimento e vértices) e envia ao SAP no commit da camada e a cada 30 segundos. Quando configurada para monitoramento por tela, o operador amostra o extent e a escala do canvas a cada 30 segundos e envia em lote. Os envios que falham por falta de rede são bufferizados e reenviados no próximo envio bem-sucedido.

## 3.29.23

Correção de bug:
- Remoção do check de finalização de Workflow quando a etapa for de revisão.

## 3.29.22

Correção de bug:
- Correção do bug de necessitar relogar no SAP Operador ao finalizar uma atividade.

## 3.29.21

Melhorias:
- Remoção do check de regras quando etapa da atividade for Revisão.

## 3.29.20

Melhorias:
- Remoção da função de remover vértice duplicado direto na camada, pois estava quebrando o Snap;

## 3.29.19

Correção de bug:
- Corrige bug de integração com o DSGTools;

## 3.29.18

Correção de bug:
- Caso o operador finalize uma atividade e não exista outra disponível, ele recebe uma mensagem na tela do QGIS, fecha o SAP Operador e limpa o projeto.

## 3.29.17

Melhorias:
- Minor fix nos textos de representação das funções.

Correção de bug:
- Correção do bug de integração com o DSGTools;

## 3.29.16

Melhorias:
- Caso a subfase tenha Regras cadastradas, a atividade só poderá ser finalizada caso as regras de Atributo Incorreto e Atributo a ser Preenchido estiverem retornando zero erro.

## 3.29.15

Melhorias:
- Aviso no caso de Carregar Camadas não existam camadas associadas aquela subfase;

Correção de bug:
- Correção do bug de carregamento do aux_grid_revisao_a;

## 3.29.14

Melhorias:
- Altera a chave do grid de revisão para considerar unidade_trabalho_id e etapa_id, conforme modelagens Topo 1.4.3 e Orto 2.5.2. Alteração feita de forma a funcionar também com versões antigas do grid de revisão.

## 3.29.13

Correção de bug:

- Corrige bug camadas incomuns;

## 3.29.12

Correção de bug:

- Atualização na forma como o getPluginsVersions() realiza a leitura das versões de plugin no metadata.txt, utilizando o cp.read_file() e não o cp.readfp();
- Atualizado a função de carregar alias para as camadas.

## 3.29.9

Melhorias:

- Altera o comportamento default da configuração da ferramenta de revisão do dsgtools para Pan to Next;

Correção de bug:

- Corrige bug de limpar o projeto ao clicar em Finalizar atividade mesmo sem confirmar os dados de login;
- Corrige bug da construção do grid de revisão ao se carregar uma nova unidade de trabalho quando a moldura está em UTM;
- Corrige bug na integração do FP com o Workflow de Validação do DSGTools: erro python com atividades sequenciais terminadas;
- Corrige bug camadas incomuns;
- Ajusta mudança de API do estatísticas de regras do DSGTools;
- Corrige carregamento de domínios;
- Corrige bug com carregamento de temas;
- Corrige tamanho de grid para produtos de grandes escalas.
- Corrige bug para carregar atividade via SAP_Gerente;
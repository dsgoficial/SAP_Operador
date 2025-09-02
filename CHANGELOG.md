# CHANGELOG

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
# CHANGELOG

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
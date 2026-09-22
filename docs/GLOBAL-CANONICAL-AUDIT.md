# GLOBAL-01 — auditoria comparativa das edições

Issue #40 · Epic #39 · observação em 22/09/2026.

## Resultado

**O padrão global deve ser composto. Nenhuma edição fornece sozinha o produto completo.** SC/Federais fornece leitura editorial, macrofiltros e coleção de consulta; SC/Estaduais, representação cadastral e de mandato; RS, histórico contextual e controle da pesquisa; PR, combinação de filtros estruturados e dois cargos na mesma engine; SP, estado de consulta normalizado, filtro efetivo de partidos e evidências focalizadas por tema.

A auditoria encontrou **sete implementações de edição**, das quais **seis no main publicado e uma somente na branch RS/Estaduais**. Há dois hubs básicos, PR e SP. Não há home geral, catálogo central de edições, hub SC, hub RS ou implementação SP/Estaduais no escopo examinado. Não se deve converter uma pasta inexistente em promessa de edição em construção.

A matriz registra **33 capacidades × 7 edições = 231 estados**, com evidência, diferenças, decisão de adoção/adaptação, dependências e testes futuros. Esses estados avaliam software e representação documental, não qualidade de candidaturas. `functional` não significa pesquisa integral, veracidade política recertificada ou conformidade completa de acessibilidade.

## Baseline e método

| Objeto | Referência congelada | Tratamento |
|---|---|---|
| main | `745cb85c9924f58ccb446714a5edf9a90d83d8c9` | Código efetivo e artefato do Pages |
| RS/Estaduais | `c2bfa3ece357f21e8aa09e32f624a9e214ad9113` | Branch isolada, PR #9, sem publicação |
| RS-FED-04A | `b124e1a7742c19fe8bc9a26fc6ebb94dfa0fb978` | PR #34: preparação, não pesquisa ou UX nova |
| SC pesquisa inicial | PR #11 ainda aberto | Registro histórico; não substitui versões posteriores do main |

O método combinou leitura dos entrypoints e scripts realmente carregados, schemas e geradores, relatórios existentes, inspeção visual de capturas e execução nova de testes sobre arquivos imutáveis. Não houve nova coleta TSE, visita às fontes políticas externas, atualização editorial ou correção de interface. Os relatórios antigos orientaram a leitura; seus totais de testes não foram somados aos desta execução.

O artefato do Pages associado ao main vem do [run 35733912623](https://github.com/selvalabs/esquerda-em-foco/actions/runs/35733912623). Ele contém 1.603 arquivos públicos; o arquivo completo do git usado nos testes contém 1.638, incluindo workflows. São conjuntos distintos. A observação de publicação se apoia nesse deploy bem-sucedido e em seu artefato, **não em uma nova conferência HTTP do site ao vivo**.

As referências abreviadas deste relatório resolvem em [evidence-index.json](../data/global-integration/evidence-index.json): cada uma identifica ref imutável, caminhos e localizadores. Estado detalhado: [capability-matrix.json](../data/global-integration/capability-matrix.json). Rotas, hashes e scripts efetivos: [current-editions.json](../data/global-integration/current-editions.json).

## Inventário real

| Edição | Rota atual | Fichas no HTML congelado | Estado de publicação |
|---|---|---:|---|
| SC/Federais | `/` | 48 | main / artefato publicado |
| SC/Estaduais | `/deputados-estaduais/` | 97 | main / artefato publicado |
| RS/Federais | `/rs/deputados-federais/` | 111 | main / artefato publicado |
| RS/Estaduais | `/rs/deputados-estaduais/` | 149 | somente branch |
| PR/Federais | `/pr/deputados-federais/` | 115 | main / artefato publicado |
| PR/Estaduais | `/pr/deputados-estaduais/` | 140 | main / artefato publicado |
| SP/Federais | `/sp/deputados-federais/` | 249 | main / artefato publicado |

São contagens de registros da interface em snapshots próprios. Não são um total nacional atualizado nem medida de cobertura política comparável entre estados. A pesquisa permanece parcial; publicação, disponibilidade de uma função e completude editorial precisam ser campos independentes.

## O que cada frente efetivamente oferece

### SC/Federais: leitura, macrofiltros e coleção — com limites de portabilidade

A camada pública atual carrega `pauta-filters-editorial.js`, além do core, dados v2 e Selecionados. A mera presença dos scripts antigos não os torna a implementação vigente. As fichas usam **Pautas atuais**, **Outras posições**, **Atuação registrada** e **Fontes e contexto**, com explicação recolhida **Neste trecho** junto ao parágrafo. A proveniência liga parágrafos a itens, associações e fontes, evitando que todas as frases recebam genericamente todas as fontes de uma ficha. [SC-UI; SC-SEMANTICS]

O modelo conserva 29 famílias em 14 grupos, 13 deles com correspondências exibidas nesse recorte. A elegibilidade `eligible_v2` é específica: apoio/prioridade atual não é qualquer ocorrência do tema, ato legislativo ou manifestação sem data. O agrupamento não atribui à candidatura todas as posições das famílias irmãs. Busca e OR/AND coexistem sem ordenar resultados por afinidade. **O trilho de partidos é navegação por âncoras, não um filtro dedicado de partidos.** [SC-UI; SC-SEMANTICS]

A coleção é escolhida manualmente, na ordem de inserção, independente dos filtros. O leitor move uma ficha original por vez e a devolve à lista, sem duplicar IDs. O link reconstrói conjunto, ordem e ficha ativa; WhatsApp e compartilhamento nativo não escolhem destinatário nem enviam mensagem automaticamente. As escolhas não são persistidas. [SC-SELECTED]

Mas há bloqueios objetivos: `selecionados.js` abandona a inicialização se a quantidade de cards ou IDs não for exatamente 48; o core fixa `sc-federais`, formato de ID, versão, limite de 256 itens importados e 4.096 caracteres. **A experiência é doadora; o código não está pronto para simplesmente ser incluído nas demais páginas.** A generalização deve testar também catálogos maiores e separar limite de transporte de limite de seleção. [SC-SELECTED, linhas 8–17 do core e 9–13 do runtime]

### SC/Estaduais: cadastro, mandato e histórico com ressalvas legíveis

A edição possui controles de partido, trajetória e situação cadastral, dados estáticos acessíveis e distinção entre exercício de mandato, licença, suplência, informação institucional e declaração não reconfirmada. Correções históricas e estados não consolidados são preservados. Essas distinções devem entrar no contrato global sem transformar dado ausente em resposta negativa. Não há ali filtros temáticos, OR/AND de temas ou Selecionados já implementados. [SC-EST]

Sua representação de transparência é útil, mas a construção ainda lê o `index.html` da raiz e extrai estilos. Substituir a raiz pela home antes de desacoplar essa leitura é um risco de regressão de build, mesmo sem editar a pasta estadual diretamente. [BUILD: `deputados-estaduais/tools/render.py`, linhas 73–75]

### RS/Federais: histórico contextual e natureza documental

RS diferencia votação nominal verificada, não verificada e não aplicável. Ausência permanece `null`, não zero; cargos de vice e suplência não recebem automaticamente votos próprios. O histórico precisa preservar município, cargo, eleição e demais elementos de contexto para evitar colisões de identidade. Sínteses e relatos têm tipos documentais e limitações, sem que todo histórico vire pauta atual. [RS-FED]

O catálogo local de 28 temas é útil para a reconciliação conceitual, **mas não constitui um filtro temático visual pronto**. Tampouco há coleção. A busca contém uma lista fixa de siglas, enquanto o runtime de RS/Estaduais já deriva as siglas dos dados. Essa melhoria da branch é candidata à reutilização sem publicar sua pesquisa. [RS-FED; RS-EST]

O gerador RS usa um HTML histórico de SC, obtido por `git show`, e só admite fallback se o hash coincidir com aquele molde congelado. Essa proteção evita uma troca silenciosa, mas também demonstra que ele não é um template global independente. [BUILD: `tools/rs/build.py`, função `template_bytes`]

### RS/Estaduais: estados da pesquisa e correções — somente em branch

A contribuição mais distintiva é separar **status de pesquisa** de **revisão efetivamente concluída na rodada**. O modelo distingue síntese com fonte individual, material revisto insuficiente, fonte bloqueada, ambiguidade de identidade e pesquisa pendente. Uma busca nominal ou resposta HTTP não é tratada como pesquisa completa. Há ainda ledger corretivo, fontes e nota pública sem apagar o registro anterior. [RS-EST]

Essas convenções são candidatas ao padrão de transparência, mas a edição continua sujeita aos gates próprios da issue #5 e do PR #9. O trabalho GLOBAL não libera sua publicação nem encerra as pendências editoriais. O gerador também depende do HTML pronto de RS/Federais. [RS-EST-BUILD; PR #9]

### PR/Federais e PR/Estaduais: consulta combinada e reconstrução de URL

Os dois cargos compartilham o runtime e combinam partido, situação, mandato, histórico e localidade documentada da atuação. A busca trabalha com termos normalizados. Os critérios se refletem na URL e podem ser reconstruídos. O recorte territorial precisa continuar significando **localidade documentada de atuação**, não residência ou base eleitoral presumida. [PR-RUNTIME]

A combinação de temas é **AND**, não um seletor OR/AND como em SC e SP. Seus temas são associados por `id`, `evidence_url` e `summary`; esse formato não oferece sozinho toda a direção e temporalidade por afirmação exigidas pelo filtro de apoio atual de SC. O catálogo local tem 25 temas e não deve ser convertido apenas por semelhança de rótulo. [PR-RUNTIME; PR-DATA]

Há cinco destinos de edição hardcoded, já insuficientes para representar o main auditado. O builder importa componentes de RS e usa o HTML gerado de RS/Federais como template. Deve-se preservar a composição de filtros e a disciplina de exports sanitizados, **não a cadeia de páginas prontas servindo de molde umas às outras**. [BUILD; PR-DATA]

### SP/Federais: estado de consulta e evidência específica por tema

SP tem filtro efetivo com multisseleção de partidos, busca por termos, OR/AND temático, validação de parâmetros, `pushState`/`popstate`, alternativa alfabética à ordem diária e compartilhamento de ficha ou consulta. Uma pauta abre as afirmações relacionadas e permite voltar ao contexto completo. A estrutura modular é doadora para separar core, dados e UI. Não há coleção Selecionados nem o mesmo fluxo dedicado de WhatsApp de SC. [SP-RUNTIME]

O produto efetivo usa **30 temas**, incluindo uma extensão de Ciência/Tecnologia, e não apenas as 29 famílias do catálogo SC. Entre as 102 afirmações em `claims_2026` há 18 com direção `apoio_ou_prioridade`, 75 `proposta` e nove `atuacao`. Esses números descrevem o schema congelado: demonstram por que **tema documentado em 2026 não equivale automaticamente a apoio atual**. A revisão externa das afirmações não foi refeita aqui. [SP-DATA]

Foi reproduzida uma lacuna de navegação: uma busca oculta as fichas e a alteração posterior do hash para uma candidatura real não a revela. O runtime só tenta rolar para uma ficha não oculta na entrada inicial. Isso não significa que todo compartilhamento individual falhe: o próprio botão individual remove a query. O defeito é a combinação entre âncora e filtro que mantém a ficha oculta. [SP-RUNTIME, linhas 153–169; finding G04]

## Diferenças que impedem uma cópia direta

1. **Trilho partidário não é filtro partidário.** SC/Federais e RS/Federais não têm a mesma função de SP, apesar de mostrarem siglas na lateral.
2. **Os filtros temáticos têm significados diferentes.** SC usa apoios atuais; SP inclui documentação temática de atuação de 2026; PR precisa de metadados adicionais por associação. O nome do botão não pode esconder essa diferença.
3. **URL compartilhável já existe, mas com contratos divergentes.** PR usa `partido` e AND temático com `replaceState`; SP usa `partidos`, modo explícito e `pushState`. SC preserva filtros em memória e só serializa a coleção quando a pessoa compartilha.
4. **Cadastro, mandato, história e pesquisa têm estados distintos.** Nenhum booleano único de pronto ou verificado pode substituir essas camadas.
5. **Os builds dependem entre si.** Mudar a home não é somente trocar um arquivo visual: afeta moldes usados por geradores.
6. **Mais documentação não significa candidatura melhor.** Contagens, lacunas e rótulos de pesquisa nunca entram como pontuação ou ordem de relevância.

## Findings e destino

| ID | Achado | Encaminhamento |
|---|---|---|
| G01 | Registry ausente; navegação entre edições divergente | #41, antes da home |
| G02 | Geradores dependem de raiz/HTML de outra edição | #41, gate de desacoplamento |
| G03 | Selecionados preso a 48 e a SC; limites de parser | #41 define contrato; #43 adapta e testa |
| G04 | SP não revela ficha ocultada quando o hash muda | #43 corrige; #44 exige regressão |
| G05 | Apoio atual, tema documentado e associação legada não equivalem | #41 modela semântica; #43 só ativa com evidência adequada |
| G06 | Serialização automática em query versus memória/compartilhamento explícito | #41 define import e privacidade; #43 migra |
| G07 | Catálogos locais de 25/28/29/30 conceitos divergem | #41 namespace/crosswalk; #43 migração revisada, sem inferência |
| G08 | Sitemap principal omite quatro rotas publicadas | #41/#42 derivam registry; #44 verifica |
| G09 | RS/Estaduais só em branch; SP/Estaduais não localizado | #41/#42 não anunciar publicação inexistente |

**G04 não foi corrigido nesta auditoria.** Os demais são gaps ou riscos constatados no código, não bugs cujo efeito tenha sido todos reproduzido. Em particular, não foi feita uma troca experimental da home para provocar falha dos builders.

## Validação realizada

[Run 35741811657](https://github.com/selvalabs/esquerda-em-foco/actions/runs/35741811657), sobre os dois refs imutáveis:

- **47 testes JavaScript existentes aprovados**, sem falhas ou skips. Suites SC filters, SC semantic v2, SC selected e SP filters.
- **140 verificações novas de navegador/preservação: 139 aprovadas e uma discrepância**, G04.
- Sete edições em 320, 360, 390, 430, 768, 1024 e 1440 px, sem overflow horizontal nas medições. Hubs PR/SP também verificados em 320/390/1440.
- Busca, limpar, filtros partidários onde implementados, menu/Escape, conteúdo e links de fontes sem JS, ausência de erros de página e coleção SC com reconstrução em um novo contexto de navegador.
- Hashes de **1.638 arquivos do main e 674 da branch RS** idênticos antes/depois da observação.
- Capturas mobile de SC/Federais, SC/Estaduais, RS/Federais, RS/Estaduais, PR/Federais e SP/Federais e desktop SC/Federais, PR/Federais e SP/Federais inspecionadas. Há 14 capturas no artefato; não se afirma inspeção manual de cada ficha ou foto.

O workflow termina com sucesso ao produzir observações, mesmo registrando um comportamento ausente. **Run verde aqui não quer dizer zero gaps.** O gate de release da #44 deverá falhar em regressões. Chromium usado: 140.0.7339.16. Requisições externas foram bloqueadas: não houve inspeção de fontes políticas externas, envio de WhatsApp, teste físico de telefone ou leitor de tela real. Não foi refeita toda suíte histórica de todas as frentes, nem executado rebuild integral delas.

## Entrega e continuação

O contrato resultante está em [GLOBAL-CANONICAL-DECISIONS.md](GLOBAL-CANONICAL-DECISIONS.md); gaps por edição, lotes e tarefas em [GLOBAL-CANONICAL-GAPS.md](GLOBAL-CANONICAL-GAPS.md). Resultados resumidos e reprodução: [qa.json](../data/global-integration/qa.json) e `tools/global01/observe.py`.

A próxima execução é a **#41**. Ela deve implementar o catálogo e os contratos, resolver a dependência de templates e a compatibilidade de URLs **antes** de a #42 substituir a raiz. Não há alteração de UI pública, migração de candidatura ou atualização eleitoral nesta entrega.

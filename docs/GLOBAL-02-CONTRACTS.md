# GLOBAL-02 · consulta, evidências e coleções

## Consulta

`assets/global/core.js` é um núcleo puro UMD, sem rede, DOM, armazenamento ou
analytics. A consulta normaliza `q`, `parties`, `topics`, `mode`, `status`,
`mandate`, `history`, `region`, `order`, `edition_id` e `semantic`.

O importador PR preserva `partido` singular e AND entre temas. O importador SP
preserva `partidos`, OR/AND e ordem explícita. Aliases são recebidos num catálogo
revisado; o núcleo não deduz equivalências por texto. Valores inválidos são
reportados em `ignored`, não transformados em categorias novas. Busca não gera
nota nem prioridade. `matches` devolve um booleano e exige mesma edição e
semântica; a ordenação continua responsabilidade do contrato da edição.

A sessão mantém mudanças em memória. Compartilhar é ação explícita e produz
`#eef=query&v=1&edition=...&state=...`. Não escreve automaticamente querystrings
com escolhas, cookies ou localStorage. Limites: texto de busca 2.048 caracteres,
fragmento 65.536 caracteres. Excesso é erro, nunca corte silencioso. Links atuais
PR/SP continuam sendo interpretados pelo importador; não se altera o comportamento
público legado neste round.

`bindQueryNavigation` reconstrói estado em `popstate`/`hashchange` e oferece
`dispose`. Uma âncora de conteúdo que não seja consulta não destrói o estado em
memória. Mudança da query legada reimporta seus critérios. Entrada versionada
inválida não substitui a sessão por uma consulta parcialmente aproveitada.

## Evidência e taxonomia

`config/taxonomies.json` conserva namespaces: SC 29 famílias, SP 30 conceitos,
RS 28 e PR 25. Cada conceito tem definição original e hash da fonte. Nenhuma
associação foi convertida. `reviewed_crosswalk` vazio significa que a equivalência
individual ainda deve ser revista, não que todas as palavras semelhantes sejam
sinônimos. Ciência/Tecnologia de SP permanece explícita.

`current_support` (apoio/prioridade atual), `documented_topic` (tema documentado,
incluindo atuação) e `legacy_context` são diferentes. Ano recente ou presença de
uma palavra não torna um ato legislativo apoio atual. `adapt_claim` exige
indicação expressa de elegibilidade pelo chamador e preserva lacunas; o adaptador
SC mantém as seções já revisadas, sem promover novo material.

`adapt_candidate` recebe identidade da edição e export público. Produz cadastro,
mandato, histórico, pesquisa, contexto, fontes, afirmações, correções e proveniência.
Não modifica a origem. Votos `null`, zero nominal verificado e não aplicável não
são intercambiáveis. `research_status` e `review_completed_in_round` permanecem
separados. Fontes que eram URLs continuam fontes, não recebem datas inventadas.
Campos privados top-level não são carregados; o contrato não é um importador de
cadastros brutos não sanitizados. Nenhuma matriz de pautas é copiada entre pessoas.

## Coleção

`createCollection` recebe edição, ano e catálogo de IDs. A ordem é a de seleção;
remover/reinserir coloca no final. Não há limite de 48, 249 ou 256 fichas. A
substituição é atômica: coleção estrangeira ou ID inválido não destrói o conjunto.
O leitor futuro terá de usar os IDs reais do DOM, sem duplicar fichas.

`collectionLink` / `parseCollection` implementam transporte v2 por fragmento.
Testes cobrem 48, 97, 149, 249, 513 e 3.000 IDs; o limite defensivo é tamanho do
link, não quantidade escolhida. Uma seleção maior que o transporte suporta
permanece na sessão; a pessoa recebe erro, não um link contendo menos itens.
O link não é secreto e conserva IDs/ordem, não uma cópia histórica do conteúdo.

Compatibilidade v1 é exclusivamente SC/2026. Arquivos `selecionados-core.js` e
`selecionados.js` já publicados não foram modificados: o novo motor só substituirá
a integração anterior na #43, com seus testes de DOM, foco e compartilhamento.
Nenhuma mensagem WhatsApp é enviada pelo núcleo ou pelas suítes.

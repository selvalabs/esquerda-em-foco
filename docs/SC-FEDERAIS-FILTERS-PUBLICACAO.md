# SC/Federais — filtros publicados e Round 2 concluído

Data: **21/09/2026**. Issue **#20**. PR **#29**.

## Estado final

Os filtros de pautas foram integrados ao `main` e a publicação foi confirmada por HTTP/SHA-256 e por interação de navegador no GitHub Pages real. Este round ativa os filtros **somente em Deputados Federais · SC**.

- Site: https://selvalabs.github.io/esquerda-em-foco/
- PR: https://github.com/selvalabs/esquerda-em-foco/pull/29
- Commit integrado: `5cb75b63526f1edd88264221339fa4d2cbf2beaf`.
- Main imediatamente anterior: `35405510d39f2534b605054a0492ffc754586f92`.
- Branch: `feat/sc-federais-filtros-v1`.
- Head aprovado: `6e7e81f17cdfe3de573c0ae14def6a07355358f0`.
- Merge candidato testado: `bb93ed87e939af7eacee1f9404d528bdaa644f64`.
- Árvore do merge candidato e da integração: `a4b32b844bd0b89e558a71cb4e47b36a81bb6cb6`.

## O que foi entregue

No desktop, **Filtrar por pautas** aparece abaixo do índice dos partidos. A sidebar continua presa durante a rolagem e possui rolagem interna para que todos os temas sejam alcançáveis entre a navbar e o rodapé.

No mobile e tablet até 980 px, o botão **Pautas · Filtrar**, junto à busca, abre um painel com os mesmos temas e seleções. O painel pode ser fechado pelo botão, por Escape ou por toque fora dele. O botão **Ver resultados** leva às fichas. Não há uma segunda lista com IDs duplicados: o mesmo painel muda de contêiner conforme a largura.

A combinação padrão é **Pelo menos uma**: Saúde e Educação, por exemplo, incluem quem tenha apoio ou prioridade documentados em qualquer uma dessas famílias. **Todas** exige correspondência em cada tema selecionado. A busca textual é aplicada junto com a escolha das pautas. **Limpar pautas** preserva a busca; **Limpar tudo**, no estado vazio, remove os dois critérios.

Há seleção visível, remoção individual de pautas, total de resultados e estado sem correspondências. Os números nos botões representam candidaturas no total desta edição, não fontes; são deliberadamente estáticos e não condicionados à busca. As categorias têm apresentação uniforme e ordem alfabética, não ordem por popularidade.

Cada ficha filtrada recebe o bloco **Neste filtro**, que explica o objeto específico do apoio ou da prioridade e apresenta as fontes pertinentes. Uma família temática não é apresentada como apoio a todas as medidas possíveis dentro dela. Nenhuma oposição isolada é convertida em apoio.

A ordenação diária permanece sob responsabilidade do código já existente. Filtrar apenas oculta ou exibe as fichas, sem classificá-las por relevância. O índice dos partidos acompanha os grupos com resultados. Links para fichas ocultadas removem os critérios de forma informada e revelam o destino; links para Fontes e contexto abrem o bloco correspondente.

Entrou também o toggle **Como funcionam os filtros de pautas**, explicando a combinação, a cobertura documental, os limites da seleção e a privacidade.

## Cobertura e limites da informação

- **48 fichas** permanecem no site e reaparecem com a busca vazia e sem pautas selecionadas.
- **26 categorias** possuem ao menos uma correspondência elegível e aparecem como botões.
- **123 associações**, em **20 fichas**, atendem ao recorte de apoio ou prioridade explicitamente documentados em 2026.
- O catálogo completo continua com **29 famílias**. As três sem apoio elegível neste recorte não viram botões vazios: `apostas-jogos`, `empresas-publicas-privatizacoes` e `politica-internacional`.

Isso não altera os resultados da pesquisa anterior: 29 fichas têm alguma evidência em algum período e 19 têm documentação acessível insuficiente. Os 20 casos filtráveis são um subconjunto mais restrito, não uma classificação de qualidade das candidaturas. Histórico, material sem período determinado e atribuição conjunta pendente continuam no conteúdo, mas não recebem elegibilidade automática no filtro atual. Oposição, debate e atuação sem apoio explícito também não são promovidos a apoio.

**Ausência de tag não significa ausência de proposta nem oposição ao tema.** Não foram pesquisadas ou atribuídas novas posições neste round; a matriz e o catálogo homologados foram preservados byte a byte. O atributo antigo `data-has-pauta` não é usado como prova de elegibilidade.

A interface consome apenas `eligible_current_support`, preservando `direction`, `position_target`, `period` e `source_ids`. Exemplo do teste público: **Saúde retorna 11 fichas**, tanto no mobile quanto no desktop.

As escolhas ficam apenas em memória. Não são gravadas em cookies, localStorage ou sessionStorage, não entram na URL e não são enviadas ao contador de acessos. A configuração de métricas existente continua desativada; este round não a habilitou.

## Validação de preparação

Run: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35645538882

Código testado: `e59538451aa34c19dd8604bf42f097085a6f3611`. Saídas compiladas: `a5b3f817d67f2008dc4cadde17a798ebc2fed485`.

**379 verificações aprovadas, zero falhas**, além do resultado detalhado dos **10 testes Node**, todos aprovados. A contagem de 379 inclui a checagem que executa a suíte Node; não deve ser interpretada como 389 verificações independentes.

A primeira execução de preparação encontrou um ponto de inserção desatualizado no texto metodológico e parou antes da publicação. O ponto de inserção foi corrigido para a versão final do Round 1; a execução aprovada acima substitui aquela tentativa. Não houve publicação da tentativa que falhou.

## Validação sobre o main atualizado

Run: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35645823603

Job `pr-validation`: **106485910682**. Resultado: **sucesso**, 379 verificações e zero falhas.

A comparação usa o main efetivo `35405510d39f2534b605054a0492ffc754586f92`, não apenas a base antiga da branch. **868 arquivos preexistentes fora das alterações autorizadas foram preservados byte a byte**. As mudanças concorrentes de RS/PR não foram sobrescritas.

O teste também confirma os 48 cards intactos, as âncoras antigas, navbar, hero, rodapé, configuração do contador, integridade das 123 associações e ausência de duplicação de IDs. O HTML fora dos blocos marcados e do adaptador de busca é idêntico ao original. A reconstrução dos arquivos gerados é idempotente.

A suíte Node cobre todas as combinações de dois temas em OR/AND, combinações de três temas, catálogo inteiro, busca normalizada, contagens por pessoa, preservação de ordens rotativas, ausência de mutação e exclusão dos registros não elegíveis.

O QA Chromium foi executado em **320, 360, 390, 430, 768, 1024 e 1440 px**: busca combinada, seleção, remoção, limpeza, resultado vazio, foco, Tab, Shift+Tab, Escape, toque fora do diálogo, mudança de breakpoint, links para fichas ocultas, abertura de fontes, navbar sticky, menu hambúrguer, ausência de overflow horizontal e de erros JavaScript. Também verificou o conteúdo sem JavaScript e a busca original quando o asset de filtros não carrega.

Artifact do QA do merge: **10660437258**, `sc-federais-filters-merge`.

Foram inspecionadas visualmente as capturas de **320 e 390 px do painel** e de **1440 px da sidebar**. Os testes bloquearam imagens externas. Não se afirma ensaio em aparelho físico, leitura com tecnologia assistiva real nem revisão visual de todas as fotos. Foram implementadas semântica acessível e navegação por teclado, com verificação automatizada correspondente.

O `data/sc-federais-filters-v1/qa.json` versionado guarda a preparação. O resultado sobre o main atualizado está no log e no artifact do PR citados acima; os dois têm 379 verificações aprovadas.

## Publicação efetivamente verificada

Run: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35646250534

Job `verify-published`: **106487327878**. Resultado: **sucesso**.

Registro de conferência: **2026-09-21T19:40:39.668323+00:00**, equivalente a 16:40:39 no horário de Brasília. **9/9 arquivos com HTTP 200 e SHA-256 idêntico ao commit integrado.**

| Arquivo | SHA-256 esperado e publicado |
|---|---|
| `index.html` | `ea171f640550fba0ac9103cee54282de2ccba0fff38fa8e4d1d6e51d251acde5` |
| `assets/pauta-filter-core.js` | `6ce62d78351d460e49494f1c47f6164b26e139b6df7e56b9fc990cf7fcc50afd` |
| `assets/pauta-filters.js` | `abfc2ccace108740df9db71a62b0ecc1f5ad818964473f502b918c9f6eaf853a` |
| `assets/pauta-filters.css` | `481fbd4867c858858b0b76341f9c551c8ffaa4877408e6db6bbb5189347c439a` |
| `assets/sc-federais-filters-data.js` | `472f353615abc7ff705ff95fdf59a298fe6b965c3ed6bfc0db9c642fe82a2cfc` |
| `data/sc-federais-filters-v1/payload.json` | `608ed8f028b61f2a093279501c1adf04e0d2d1d77aaf438d4418ff568f102e69` |
| `data/sc-federais-filters-v1/manifest.json` | `5292f3db6188fe27ccd2a2362c2c59e422c9aa31d94d6be71fb83b7ae79f25e0` |
| `config/topics-v1.json` | `c042916a25c2e8a25eea0b735421630e13385183e4d66e56510e2680c8bfdaf4` |
| `data/sc-federais-topics-v1/matrix.json` | `6c6153a081bbdda250ebff97b23798e8c896c1e999461a44968f5b913e1a55fb` |

Após a conferência de arquivos, o navegador abriu o endereço público em **390 e 1440 px**, encontrou 48 fichas sem seleção, selecionou Saúde e confirmou 11 resultados. As duas larguras passaram, sem erros JavaScript ou overflow horizontal. No mobile, o diálogo abriu e fechou com Escape.

Artifact: **10660248355**, `sc-federais-filters-live`; relatório `eef-sc-federal-filters-live.json`. SHA-256 do ZIP: `0c61247d547060b5296f75f38ce8572359bdf1f94b2d1dc5c47a87d22f18ddcb`.

## Fechamento e replicação

O escopo dos dois rounds da #20 está entregue: base documental integrada, taxonomia versionada, associações rastreáveis, filtros desktop/mobile, transparência, QA e publicação conferida. Isso não elimina as lacunas documentais nem afirma completude de programas de todas as candidaturas.

A documentação de arquitetura, reprodução e replicação está em `docs/SC-FEDERAIS-FILTERS-V1.md`, em conjunto com `docs/TOPICS-V1-CONTRACT.md`. As demais frentes não receberam os filtros nesta entrega. Para replicar, devem fornecer suas próprias matrizes aprovadas, recalcular contagens e cobertura e executar os testes sobre a base efetiva, sem copiar associações entre pessoas ou legendas.

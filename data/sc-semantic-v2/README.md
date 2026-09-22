# SC Federais — dados semânticos v2

Entrega de dados/modelo editorial do Round 1 da issue #32. **Não ativa a interface v2.**

- `association-audit.json`: decisões sobre todas as 156 associações originais, incluindo as 123 antes elegíveis.
- `candidate-content.json`: modelo das 48 fichas, com blocos separados e fontes resolvíveis.
- `source-review.json`: reconferências, localizadores, atribuição e indisponibilidade explicitada.
- `family-audit.json`: as 29 famílias preservadas e a fila de avaliação de lacunas.
- `macrogroups.json`: 14 grupos amplos propostos, sem propagação de apoio entre famílias.
- `coverage.json`: contagens calculadas por pessoa e associação, não medidas de mérito.
- `qa.json`: resultado da preparação; o QA sobre a base efetiva do PR fica também no artifact do respectivo run.

## Integração no Round 2

O renderer deve consumir `match_text` como frase completa, sem acrescentar “apoia + categoria”. O conteúdo principal vem de `sections`, e cada item mantém fontes e associação. `contexto` fica em Fontes e contexto; não converter material sem data em histórico com ano inventado.

Apenas `eligible_v2` alimenta os futuros filtros de pautas defendidas. O agrupamento público usa os macro IDs, mas não cria novas associações. “Todas” exige correspondência própria em cada macrogrupo. Contagens são uniões de pessoas distintas.

Os campos e arquivos v1 permanecem como proveniência e **não devem ser reutilizados silenciosamente como elegibilidade v2**. As 19 lacunas da pesquisa anterior não foram refeitas neste round. Uma fonte histórica não pôde ser reconfirmada e permanece com ressalva.

Não há mudança em index.html, assets, dados eleitorais, navbar, rotação, rodapé ou outras frentes. QA visual/funcional e publicação dos novos filtros pertencem ao Round 2.

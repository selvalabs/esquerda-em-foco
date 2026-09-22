# SC Federais — interface semântica v2 publicada

**Round 2 da issue #32 concluído em 22/09/2026.** O frontend v2 foi integrado pelo PR #35 e conferido no endereço público. O recorte documental continua datado de 21/09/2026; esta implementação não realizou nova pesquisa de candidaturas.

Site: https://selvalabs.github.io/esquerda-em-foco/

## Integração e proveniência

- PR: https://github.com/selvalabs/esquerda-em-foco/pull/35
- Base preservada: `a815c909fa8551ed351e637ab0efb63390af6e19`.
- Branch de implementação: `feat/sc-federais-semantica-v2-ui`.
- Head aprovado do PR: `6b199078935f0e1c1191cd28cf03ea8d852ed75e`.
- Merge candidato testado: `9bb47dfc3c7d1691160c47f1163fd6aec7bc531d`.
- Commit de integração: `a6103d2a7718ccc5a20a99a99da0b82015e1125d`.
- Correção posterior somente no teste de publicação: `5c9692d334b7b9fada3e2ba9663b2c0e0b90c064`.

A correção posterior não alterou HTML, CSS, runtime, payload ou modelo documental. Os 11 arquivos públicos verificados têm os mesmos hashes nas duas conferências. As entradas v1 e a auditoria v2 permanecem preservadas.

## Resultado visível

As 48 fichas agora apresentam os blocos não vazios do modelo revisado: **Pautas defendidas**, **Posições públicas** e **Histórico de atuação**. Material sem período ou atribuição confirmados fica em **Contexto documental**, dentro de Fontes e contexto. Não há blocos vazios nem conversão automática de documento sem data em histórico.

As referências numeradas levam à fonte correspondente dentro da ficha. O bloco opcional **Ver evidências por bloco** conserva as afirmações individuais e suas referências, sem obrigar a exibir toda a auditoria na leitura inicial.

Os filtros foram substituídos por **13 áreas amplas com correspondências**, dentre **14 grupos que preservam as 29 famílias internas**. **O que cada filtro reúne** mostra todas as famílias e também Relações internacionais, preservada sem botão vazio obrigatório. As famílias não são apagadas ou automaticamente atribuídas umas às outras por compartilhar um grupo.

No desktop, o painel fica abaixo dos partidos, com rolagem interna. No mobile/tablet, o mesmo painel é aberto pelo botão Pautas · Filtrar. OR/Pelo menos uma, AND/Todas, busca combinada, remoção individual, limpar e estado vazio foram mantidos. A ordem continua sendo a rotação diária, sem ranking por quantidade de temas.

**Por que aparece neste filtro** mostra grupo, família e frase concreta com a fonte. No caso de Jú, em Economia e Estado, a correspondência tributária aparece como **Defende impostos proporcionais à renda e ao patrimônio.** Não há fórmula automática de apoio a toda uma categoria nem afirmação sobre regularidade fiscal ou declaração de bens.

## Cobertura aplicada

O frontend usa somente as **112 associações eligible_v2, em 19 candidaturas**. As 11 associações reclassificadas pela auditoria não alimentam o filtro positivo; seu conteúdo foi mantido em atuação ou posições públicas. Nenhuma associação inelegível foi promovida para preencher grupos.

As 48 candidaturas continuam disponíveis com os critérios limpos. As 19 candidaturas com correspondências atuais não se confundem com as 19 lacunas documentais do levantamento anterior. **Ausência de tag não significa ausência de proposta ou oposição.** Esta entrega não garante completude de programas nem valida automaticamente resultados alegados pelas campanhas.

| Filtro amplo | Candidaturas no recorte |
|---|---:|
| Agricultura e campo | 3 |
| Cidades e infraestrutura | 6 |
| Cultura | 6 |
| Democracia e liberdades | 8 |
| Direitos e igualdade | 8 |
| Economia e Estado | 4 |
| Educação, infância e juventude | 10 |
| Meio ambiente e proteção animal | 5 |
| Mulheres e cuidado | 12 |
| Povos e territórios | 2 |
| Saúde | 10 |
| Segurança e justiça | 2 |
| Trabalho e renda | 10 |

As contagens são pessoas distintas por grupo, não fontes, e não devem ser somadas como população total. Elas não variam com a busca e não ordenam os resultados. Relações internacionais tem zero associação de apoio atual elegível neste recorte, mas seu material continua na base e nos contextos correspondentes.

## QA antes e durante a integração

Preparação: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35715431161

Merge candidato: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35715869226

As duas execuções aprovaram **649 verificações, zero falhas**, incluindo a execução de **nove testes Node**, também todos aprovados. Não são 658 verificações independentes. Na comparação com a base efetiva do PR, **957 arquivos preexistentes fora das mudanças autorizadas foram preservados byte a byte**.

A validação inclui os 48 cabeçalhos, redes, trajetórias e âncoras; todas as 112 correspondências exatas de texto/família/grupo/fonte; a exclusão das 11 reclassificações; os resumos aprovados e os itens de evidência; construção idempotente; contagens por pessoa; ausência de propagação entre famílias e preservação dos dados das demais frentes.

O motor foi testado contra a auditoria independente em todas as combinações de um, dois e três grupos em OR/AND e no catálogo inteiro. O QA de navegador usou Chromium em **320, 360, 390, 430, 768, 1024 e 1440 px**, cobrindo busca, filtros, limpar, vazio, foco, Tab/Shift+Tab, Escape, fechamento externo, mudança de breakpoint, links para fichas ocultas, fontes, navbar, rotação e falhas de assets/JavaScript.

Capturas do painel em 320 px, dos blocos em 390 px e dos filtros/fontes em 1440 px foram inspecionadas. A separação entre os blocos foi corrigida para continuar visível após limpar filtros. Um teste de foco foi ajustado para aguardar o evento assíncrono nativo de fechamento do diálogo, sem retirar a exigência de devolver o foco.

Artifact do merge: **10688609794**, `sc-semantic-v2-ui-merge`. SHA-256 do ZIP: `e556105a303e74ce27d6840d720c72fe99468fdd36ec170947fb9e2346528f40`.

## Prova da publicação

Run aprovado: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35716105097

Job `verify-published`: **106707868944**, concluído com sucesso.

Conferência registrada em **2026-09-22T10:28:16.234642Z**. Os **11/11 arquivos** responderam HTTP 200 e coincidiram em SHA-256 com o commit verificado. Depois, o navegador acessou o GitHub Pages em **390 e 1440 px**, confirmou 48 fichas iniciais, 13 filtros, quatro resultados em Economia e Estado e a frase tributária correta de Jú. A busca “impostos proporcionais”, combinada ao grupo, retornou somente a ficha `240002533832` nas duas larguras.

Também foi confirmado que o relato histórico de voto sobre 6×1 de Ana Paula Lima não aparece como justificativa do filtro de Trabalho e renda. Não houve erros JavaScript ou overflow horizontal nesses ensaios.

A primeira conferência pública já havia validado os 11 arquivos, mas falhou em uma expectativa incorreta do próprio teste: a busca textual “Jú” foi tratada como nome exclusivo, embora a busca também encontre “jurídica” e “justiça”. O teste passou a usar uma frase inequívoca e a conferir o ID exato, sem mudar o comportamento do site. A prova válida é a execução aprovada indicada acima; a falha anterior não foi ocultada nem contabilizada como sucesso.

Artifact: **10688514629**, `sc-semantic-v2-ui-live`, com relatório e capturas. SHA-256 do ZIP: `48db66903d43e85ae7a1cc5c6066567859b89ef87cf93b7612f8e3f1f3058aa5`.

| Arquivo | SHA-256 publicado |
|---|---|
| `index.html` | `3f5e519e2a023525c912aa5165809956332973ae1eb819e6f95390074c9446a3` |
| `assets/pauta-filter-core.js` | `6ce62d78351d460e49494f1c47f6164b26e139b6df7e56b9fc990cf7fcc50afd` |
| `assets/pauta-filters.css` | `481fbd4867c858858b0b76341f9c551c8ffaa4877408e6db6bbb5189347c439a` |
| `assets/pauta-v2.css` | `95309a77adc7f31657f9c214de7b3cd6c624fdf4b01072b0a1185e2b78f1d06c` |
| `assets/pauta-filters-v2.js` | `06ad500223e05de752186429fd0b40d549d02d21e0936d61d3266ce99548c41a` |
| `assets/sc-federais-filters-v2-data.js` | `0a2ac880d0f82b6a7ed7e89066a7e52c1a46e52e698d519550213c9ad5adcc86` |
| `data/sc-semantic-v2-ui/payload.json` | `ac3b31e47daf45b090fff9f5a7e25a20eaf03f40f14a03836b4857d784841f2b` |
| `data/sc-semantic-v2-ui/manifest.json` | `062d2741952a6f4920459136bba453c62e45c93c0d80b546c80111b69402b47b` |
| `data/sc-semantic-v2/candidate-content.json` | `a547de0cd21cdce7ab57307f99fdd924b377ba8387230fe1c453a76420089d83` |
| `data/sc-semantic-v2/association-audit.json` | `41bd9a6fbdb08abe6ff44bcf65fe3c9ce46294a190e1114c01373b537ddf9d1b` |
| `data/sc-semantic-v2/macrogroups.json` | `fbe9d6dadd084da53edbd6d5126dc8149f900cbb75b9308d036d4b8721bbd940` |

## Limites e continuidade

Os ensaios bloquearam fontes/imagens externas. Não equivalem a teste em aparelho físico, inspeção de todas as fotos ou uso de leitor de tela real. Foram implementadas e testadas semântica e navegação por teclado; o QA não certifica interpretações políticas.

As escolhas de filtro permanecem em memória, sem armazenamento, parâmetros de preferência na URL ou envio à API de métricas. O contador continua desativado. A navegação, a rotação, o hero, o rodapé, as redes e os dados eleitorais foram preservados. Nenhuma outra edição recebeu estes filtros.

A #32 está entregue nos seus dois rounds: auditoria/modelo via PR #33 e interface/publicação via PR #35. A implementação está pronta como referência técnica para replicação, sempre com matrizes próprias e revisão documental das demais frentes. As lacunas não foram eliminadas por esse fechamento.

Arquitetura e reprodução: `docs/SC-FEDERAIS-SEMANTICA-V2-UI.md`. Modelo de origem: `data/sc-semantic-v2/README.md`. Estado da interface: `data/sc-semantic-v2-ui/manifest.json`.

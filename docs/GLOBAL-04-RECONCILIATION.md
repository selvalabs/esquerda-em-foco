# GLOBAL-04D5 · reconciliação final

Baseline do produto: `8a36b2a47a893746ea528646ff0bb40d6a2d9101`. Issue #57; mãe #43; epic #39.

## Conclusão

As seis edições têm a mesma composição funcional. Diferenças de cobertura não significam seis sistemas de interface. O encerramento funcional não conclui pesquisas editoriais, a #44 ou a #50. Fechar a issue somente depois do gate público de metadados.

## Matriz operacional

| Edição | Fichas | Temas: atual / documentado / contexto | Registro | Aptidão | Mandato | Histórico | Localidade |
|---|---:|---|---|---|---|---|---|
| 2026-sc-federais | 48 | 25 / 27 / 8 | Sem base estruturada | Sem base estruturada | Disponível | Disponível | Sem base estruturada |
| 2026-sc-estaduais | 97 | 0 / 0 / 0 | Disponível | Sem base estruturada | Disponível | Disponível | Sem base estruturada |
| 2026-rs-federais | 111 | 0 / 0 / 27 | Disponível | Sem base estruturada | Disponível | Disponível | Sem base estruturada |
| 2026-pr-federais | 115 | 0 / 0 / 16 | Disponível | Disponível | Disponível | Disponível | Disponível |
| 2026-pr-estaduais | 140 | 0 / 0 / 15 | Disponível | Disponível | Disponível | Disponível | Disponível |
| 2026-sp-federais | 249 | 0 / 30 / 0 | Disponível | Sem base estruturada | Disponível | Disponível | Sem base estruturada |

Os totais temáticos contam conceitos com vínculos existentes, não candidaturas aptas ou mérito. As contagens por candidatura no JSON não devem ser somadas entre recortes.

SC Estadual conserva textos e fontes, mas não tem matriz temática individual revisada. Painel de fonte não autoriza associação candidato→tema. RS/PR mantêm contexto; SP mantém documentação temática; SC Federal tem os três recortes. Localidades com atuação documentada existem somente no PR nesta baseline.

## Divergências e decisões

- A01/A02/A03 e outras capacidades do catálogo operacional ainda carregavam estados da auditoria inicial. Foram reconciliadas; o inventário histórico não foi reescrito.
- O campo `reason` do payload D4 é fallback para controle desabilitado, não diagnóstico de bloqueio quando a dimensão está ready. O relatório D5 separa `blocking_reason` de `limitation` sem mudar o runtime.
- E01 conserva granularidade: afirmação individual em SC Federal/SP; síntese inteira ou fontes narrativas nas demais. Nenhum vínculo frase→fonte foi inventado.
- E05/E06 são específicos de origem: correções e exports legados não foram substituídos por formatos públicos únicos. O modelo interno comum não é alegado como export público novo. Versões substituídas não são reintroduzidas como posições vigentes.
- Q02/Q04 permanecem parciais para a #44. Foco/noJS e bytes já testados não equivalem a certificação integral de acessibilidade ou SEO.
- Identidade é por candidatura/eleição/UF/cargo, não pessoa universal. #50 não foi implementada.

## Preservação e manutenção

Este round modifica catálogo de capacidades, status de migração, hash desse catálogo no manifesto e o teste que reconhece o fechamento D5. Páginas, JS/CSS, textos, fontes, fotos, associações e snapshots permanecem byte a byte iguais ao rollout. O teste protege todos os demais arquivos preexistentes.

O gerador D5 é determinístico. baseline/lot/editions no status conservam o contexto do lote 02; canonical_rollout registra D4; reconciliation é o fechamento atual. As 33 capacidades têm estado, justificativa e disposição no JSON. Nova pesquisa exige nova baseline, não restaurar este snapshot sobre conteúdo posterior.

## Evidências e publicação

Evidência D4 preservada: run 35844058016, artefato 10742911162, SHA-256 25994b1eaf8619d57af4ec163462b86eb116febaa4d857c59ff0b08a637e2a52. Não é execução D5. O workflow D5 registra testes, preservação e verificação pública próprios no artefato e na issue/PR.

Antes do merge, HTTP usa o manifesto da baseline publicada. Depois do merge, usa o novo manifesto, incluindo o catálogo reconciliado. Nunca exigir um hash ainda não publicado nem aceitar catálogo antigo como aprovação pós-merge.

A #43 pode fechar após a #57; o epic #39 só depois da #44. Sem pesquisa externa nova, mensagem WhatsApp real, preferências persistentes ou teste em aparelho físico.

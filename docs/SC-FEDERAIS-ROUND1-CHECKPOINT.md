# SC Federais — checkpoint do Round 1

## Preparação validada em 21/09/2026

PR #24, continuidade das issues #6 e #20.

O run https://github.com/selvalabs/esquerda-em-foco/actions/runs/35642442416 concluiu a preparação com **296 verificações aprovadas e zero falhas**. Comparação inicial: `38e66f643048a00f15a70d6f7be3a69e83cf4c23`; 685 arquivos preexistentes, além do index, foram preservados byte a byte. O index teve somente alterações de pautas, contexto, método e inclusão do CSS correspondente.

Entregáveis: 48 fichas, 29 com alguma evidência e 19 com lacuna; 29 famílias; 156 associações vinculadas a 52 grupos de afirmações e 36 fontes. Há 131 associações de posições individuais situadas em 2026 e 123 de apoio/prioridade explícitos nesse recorte. As 21 fichas do primeiro conjunto e as 20 do segundo não são notas ou classes de mérito.

As 36 URLs da revisão possuem registro de disponibilidade/proveniência. Nenhuma resposta 404/410 ficou pendente no teste. As leituras de redes sociais do round anterior não foram repetidas automaticamente; seu run de verificação permanece registrado.

## Integração ainda em validação neste checkpoint

O main avançou para `cb0617c6728739e5a0b85ff30398c67d138b0301`, com mudanças de SC estaduais. O PR está configurado para testar o merge candidato contra a base efetiva e preservar essas mudanças. O encerramento depende do resultado desse teste e da conferência dos bytes servidos pelo GitHub Pages; commit ou PR aberto não comprovam publicação.

## Observação para o Round 2

`data-has-pauta` no HTML significa existência de alguma síntese, inclusive histórica. **Não é um sinal de elegibilidade para os filtros atuais.** Usar a matriz v1 e seus campos `eligible_current_position` e `eligible_current_support`, conservando objeto, direção, período e fonte.

O `qa.json` da pasta `sc-federais-pautas` é histórico da pesquisa. O relatório de integração desta rodada está em `data/sc-federais-topics-v1/integration-qa.json`, e o QA do merge fica no artifact do PR. A comprovação final de publicação será registrada nas issues e no relatório de encerramento.

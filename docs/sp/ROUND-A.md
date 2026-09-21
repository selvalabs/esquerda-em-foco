# SP · Deputados federais · Round A

**Gate eleitoral: BLOCKED**

- Coleta: 2026-09-21T17:42:21.850312+00:00
- Baseline: `810a7896b3355254d50852761a41bae31ce3f567`.
- Universo federal SP: **1131** registros.
- Recorte do projeto: **234** registros.
- Fora do recorte partidário: **897** registros, preservados na auditoria.

## Recorte por partido

| Partido | Registros |
|---|---:|
| PCO | 10 |
| PCdoB | 2 |
| PDT | 58 |
| PSB | 71 |
| PSOL | 36 |
| PT | 49 |
| PV | 3 |
| UP | 5 |

## Situação oficial

| Situação | Registros |
|---|---:|
| #NE | 234 |

## Critérios e limites

Ano 2026, UF SP, cargo 6. Oito siglas herdadas de SC/RS, comparação sem distinção de caixa. Nenhuma candidatura é retirada devido à situação do registro. O recorte é operacional e não classifica ideologicamente siglas externas.

Nomes e números são preservados da fonte. Identificadores são strings. Localidade estadual não é tratada como município de residência. Resultado e votos de 2026 permanecem nulos; listas históricas vazias significam pesquisa não iniciada, não ausência de participação anterior.

O contrato mantém os campos do schema v1 do RS e acrescenta proveniência, situação detalhada e estados explícitos de pesquisa. CPF, título, data de nascimento e outros campos desnecessários não são exportados.

## Taxonomia e dependência upstream

A taxonomia revisada de SC não é declarada homologada nesta rodada. `data/sp/taxonomy.lock.json` registra a referência upstream. Nenhuma tag individual foi atribuída. Essa dependência deve ser resolvida antes da classificação do Round B.

## Auditoria

- Identificadores únicos no recorte: 234.
- Informações complementares ausentes: 0.
- Complementos duplicados: 0.
- Registros com situação diferente de deferido: 234.
- Arquivos protegidos conferidos: 330.
- Arquivos protegidos alterados: 0.
- Problemas bloqueantes: 234.

Consulte `reconciliation.json` para conflitos, substituições, números reutilizados e prova de isolamento. Consulte `manifest.json` para URLs, hashes completos e horários de geração de cada fonte. Os localizadores usam ordinal de registro CSV (cabeçalho = 1), não número de linha física.

## Fontes

- [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/dataset/candidatos-2026).
- [Candidaturas 2026](https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip).
- [Informações complementares 2026](https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand_complementar/consulta_cand_complementar_2026.zip).

## Próximas etapas (não executadas)

Round B: reconciliar a taxonomia upstream, pesquisar perfis em lotes e atribuir pautas com evidências. Round C: integração, regressão de interface e publicação. Nenhum frontend, rota, navbar ou arquivo de SC/RS/PR foi modificado por este pipeline.

# SP federais — Round B: checkpoint documental

**Validação técnica: PASS. Revisão editorial: PARCIAL. Publicação: NÃO LIBERADA.**

Esta entrega não encerra a pesquisa individual dos 234 registros. Coleta oficial, identidade, conteúdo revisado e pendências são contabilizados separadamente.

## Cobertura

- candidate_records: **234**.
- official_profiles_verified: **234**.
- official_photos: **234**.
- social_declaration_candidates: **215**.
- prior_election_candidates: **176**.
- prior_election_records: **555**.
- current_year_rows_excluded_from_history: **81**.
- individual_research_entries: **45**.
- candidates_with_reviewed_editorial_sources: **34**.
- candidates_with_biography: **33**.
- candidates_with_topic_evidence: **21**.
- topic_evidence_records: **50**.
- reviewed_source_records: **47**.
- unique_reviewed_urls: **47**.
- candidates_without_individual_editorial_review: **189**.
- current_role_observations_reviewed: **3**.
- documentary_topics: **29**.
- active_product_topic_assignments: **0**.

## Cobertura por partido

| Sigla | Registros | Entradas de pesquisa | Biografias | Com evidência temática |
|---|---:|---:|---:|---:|
| PCO | 10 | 10 | 10 | 6 |
| PCdoB | 2 | 2 | 1 | 1 |
| PDT | 58 | 11 | 2 | 1 |
| PSB | 71 | 3 | 3 | 3 |
| PSOL | 36 | 3 | 3 | 3 |
| PT | 49 | 8 | 8 | 3 |
| PV | 3 | 3 | 2 | 2 |
| UP | 5 | 5 | 4 | 2 |

As diferenças de cobertura são lacunas de pesquisa, não avaliações de candidaturas. A ordem é a do recorte do projeto, não de preferência política.

## Proveniência e interpretação

Os 234 registros continuam sendo os do Round A. Nenhum foi removido por renúncia ou julgamento. O histórico separa eleições anteriores de linhas do próprio pleito de 2026. Votos históricos ausentes não são zero. A identidade foi conferida no DivulgaCand por ID e nome civil; o número também foi comparado no build.

Cada evidência temática registra candidato, tema, medida, autoria/declaração, direção, temporalidade e fonte. Menção a tema não implica apoio a toda medida associada. Conteúdo sem data não ganhou uma data de publicação inventada. As associações documentais não foram ativadas como filtros de apoio atual.

A proposta de SC foi fixada como versão documental reutilizável, com Saúde separada de apoio específico ao SUS. Nenhum arquivo de taxonomia ou associação de SC/RS/PR foi alterado. O erro inicial de parser do DivulgaCand foi corrigido e a verificação individual repetida; o arquivo de tentativas anteriores foi preservado.

Uma formulação de situação difere entre o extrato e o perfil: o extrato abrange prazo recursal ou recurso, enquanto o perfil usa uma descrição mais curta. Ambos os textos estão disponíveis em audit.json e nos dados, sem alteração retroativa da fotografia A.

## Pendências de encerramento

research-queue.json e coverage.csv identificam cada candidato e cada lacuna. Ainda é necessário concluir as pesquisas individuais pendentes, aprofundar as fichas parciais, confirmar cargos atuais não verificados e conferir links sociais individualmente. A API da Câmara não respondeu no runner após tentativas registradas; fatos obtidos no portal público foram atribuídos à fonte específica.

## Arquivos

`normalized.json`: base enriquecida; `sources.json`: fontes editoriais; `evidence.json`: relações documentadas; `research-queue.json`: fila nominal; `audit.json`: testes e contagens; `taxonomy.json`: contrato documental; `inputs/`: pesquisa revisada versionada.

As fontes oficiais e seus hashes ficam em collection.json e supplement.json. As fontes individuais, com URLs e localizadores, ficam em sources.json. Não houve frontend, merge ou deploy.

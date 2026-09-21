# SP federais — Round B final

**Data: 21/09/2026. Gate editorial/documental: PASS. Gate técnico: PASS. Frontend/filtros: NÃO ATIVADOS.**

## Resultado consolidado

A população eleitoral permanece a do Round A: 234 registros no recorte operacional do projeto. Todos os 234 receberam revisão individual no protocolo do Round B.

A camada editorial final contém:
- 234 fichas únicas revisadas;
- 48 candidaturas com ao menos um claim documentado;
- 42 com pelo menos um claim identificável no ciclo de 2026;
- 6 com evidência apenas histórica ou sem data confiável;
- 186 fichas em que a pesquisa não localizou evidência individual suficiente para síntese temática;
- 112 claims, dos quais 102 em 2026, 3 históricos e 7 sem data;
- 75 fontes registradas, todas com URLs distintas;
- 218 associações candidato–tema sustentadas por claims de 2026.

Esses números medem **cobertura documental**, não qualidade, alinhamento, prioridade política, força de candidatura ou recomendação eleitoral. Ausência de claim não significa oposição ou ausência de posição.

## Camada técnica reconciliada

O checkpoint técnico da issue #12 foi incorporado à branch final por meio do PR #22. Ele preserva:
- 234 perfis individuais conferidos no DivulgaCand;
- 234 fotografias oficiais vinculadas por identificador e verificadas estruturalmente;
- 215 pessoas com redes/sites declarados ao TSE;
- 176 pessoas com 555 registros eleitorais anteriores a 2026;
- separação de 81 linhas do pleito atual que aparecem no arquivo de histórico;
- 24 testes e uma validação independente do artefato, com hashes e reconstrução determinística.

Esse checkpoint foi produzido antes da conclusão da pesquisa editorial: seus arquivos de evidência e cobertura parcial permanecem versionados por proveniência, mas **não são o índice editorial final**.

## Arquivos canônicos para a pesquisa editorial

- `data/shared/pautas-taxonomy-v1.json`: vocabulário controlado de 30 famílias para pesquisa.
- `data/sp/research/records.json`: 234 fichas editoriais consolidadas.
- `data/sp/research/theme-evidence-2026.json`: apenas associações sustentadas por claims do período 2026.
- `docs/sp/ROUND-B-AUDIT.json`: auditoria final.
- `docs/sp/ROUND-B.md`: relatório resumido.
- `data/sp/research/batch-01.json` a `batch-05.json`: lotes de pesquisa versionados.

Os arquivos em `data/sp/round-b/` e `docs/sp/round-b/` preservam o checkpoint técnico/independente da issue #12. Quando houver divergência de cobertura editorial, os arquivos canônicos acima prevalecem para o Round B final.

## Método

Nenhuma pauta foi atribuída por partido, profissão, nome de urna ou biografia. Cada claim aceito registra fonte, tema, temporalidade, direção e tipo de evidência.

Material de campanha é tratado como declaração/proposta da candidatura, não como comprovação de implementação. Atuação legislativa é registrada como ação documentada e não implica concordância com toda a família temática. Conteúdo histórico e sem data permanece separado do índice de 2026.

A taxonomia documental de SC foi usada como ponto de partida. A categoria ampla de saúde substitui a formulação que poderia implicar automaticamente apoio ao SUS em toda menção de saúde. Foi acrescentada a família geral de ciência, tecnologia e inovação para cobrir uma lacuna do vocabulário; nenhuma candidatura recebeu essa categoria por profissão ou formação.

## GitHub e validação

Branch final: `feat/sp-federais-round-b`.

- Bootstrap oficial: workflow 35639459993 — PASS.
- Auditoria editorial: workflow 35642124028 — PASS em consolidação, integridade, isolamento e gravação.
- Reconciliação do checkpoint técnico: PR #22, merge `3abdc9274d736ef9dc52af3313df1f4bfd284b1b`.
- Issues: #12 (checkpoint técnico parcial) e #15 (Round B final).

A auditoria final verificou 234 registros únicos, correspondência exata com a fila eleitoral, referências de fontes, IDs de claims, IDs da taxonomia, períodos, tipos de evidência e ausência de claims em fichas classificadas como documentação insuficiente. Nenhum problema de integridade permaneceu.

## Limites

A pesquisa não pretende provar inexistência de propostas quando uma ficha ficou sem claim. Sites, redes ou materiais podem surgir ou mudar depois da data da revisão. As evidências registradas devem ser atualizadas quando houver nova documentação relevante.

Votos e resultados da eleição de 2026 continuam nulos antes do pleito. A pesquisa não produz ranking, score, recomendação ou previsão eleitoral.

## Próximo round

O Round C pode consumir exclusivamente o índice `theme-evidence-2026.json` para construir filtros explicáveis no produto, preservando a possibilidade de mostrar a evidência que justifica cada associação. Histórico e conteúdo sem data não devem ativar automaticamente filtros de posição atual.

**Nenhuma rota, filtro, navbar, página de SP, merge em main ou deploy foi executado neste Round B.**

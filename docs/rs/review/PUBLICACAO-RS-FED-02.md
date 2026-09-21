# RS-FED-02 — publicação verificada

Consulta documental: **21/09/2026**. Publicação verificada em **21/09/2026, 18:22:31 UTC (15:22:31 de Brasília)**. A base não é atualizada em tempo real.

## Versão

- Página: https://selvalabs.github.io/esquerda-em-foco/rs/deputados-federais/
- PR integrado: https://github.com/selvalabs/esquerda-em-foco/pull/14
- Commit de integração: `b52b5b853a6887b7c13ab715a4c6bb585ed267c8`.
- Main imediatamente anterior à integração: `e1e5539463b0f0641b5790a8506f521b591c7d4e`.
- Commit usado na conferência pública: `903b0d3720ae6a0a3b191767e1046bc3e796d976` (acrescenta apenas a configuração da conferência).
- SHA-256 do HTML efetivamente servido: `615bc7c6a7f9a1e008b1cdc4f5ce2e014c749803d69c05d8df5a5ab1359d7c70`.

## Cobertura editorial real

107 fichas e perfis eleitorais reconferidos. O cadastro continua com 106 deferidos e uma renúncia identificada; não significa 107 candidaturas ativas.

As sínteses individuais passaram de 28 para **46**: **44 sobre pautas ou atuação documentada e duas apenas de trajetória**. **61 fichas ainda não possuem síntese suficiente**. Considerando exclusivamente pautas/atuação, há 63 fichas sem essa síntese (as 61 mais as duas com trajetória apenas). Não contabilizar uma biografia ou um aviso de informação insuficiente como programa de campanha completo.

Há **22 biografias documentadas** e **16 cargos eletivos confirmados**, ante nove na primeira entrega. A revisão dos cargos estaduais e municipais não é exaustiva. Um campo não confirmado não significa ausência de cargo.

Permanecem **82 fichas com histórico anterior**. A cobertura de alguma votação nominal anterior passou de 80 para **81 fichas**. São **276 registros nominais reconciliados**, **21 casos em que a votação nominal individual não se aplica** e **oito registros ainda não reconciliados**. Valores ausentes não foram convertidos em zero.

Há **28 temas documentais**, associados com fontes a 44 fichas. Não foram criados filtros visuais novos. Os registros mantêm o período e distinguem declaração de campanha, ato legislativo, realização documentada e trajetória.

O controle da revisão cobre as **107 fichas**, com **87 registros de consultas individuais** e referências/limitações específicas. Foram registrados 48 exames de disponibilidade de fontes e revisadas as **15 declarações de endereço rejeitadas** após a validação mais estrita. **Zero substituições de canais foram presumidas.** Um bloqueio de consulta não foi tratado como prova de inexistência da página.

## Testes e comprovação

Validação da branch: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35637303970

- **35 testes unitários passaram**, cobrindo dados, referências, privacidade, históricos, temas, metadados e idempotência.
- **171 verificações Chromium passaram**, nas larguras 320, 360, 390, 430, 768, 1024 e 1440 px.
- Busca, menu, âncoras, recarga de link individual, 107 fotografias, recursos locais e rotação diária passaram.
- O overflow de 13 px em 320 px foi corrigido nos fundos decorativos, sem ocultar texto dos cards ou aplicar ocultação ao corpo inteiro.
- Dois builds consecutivos produziram arquivos com hashes idênticos.

Deploy Pages: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35637949635 — build e deploy concluídos com sucesso.

Conferência pública: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35637950408

- **120 arquivos responderam HTTP 200 e coincidiram em SHA-256 com o commit verificado**, incluindo todas as saídas da rota RS, o HTML federal de SC, a página estadual de SC, sitemap e robots.
- Zero diferenças inesperadas fora dos arquivos próprios do RS e dos três workflows exclusivos dessa revisão no merge de implementação.
- A comparação usou o **main efetivamente anterior ao merge**, preservando as alterações concorrentes nas demais frentes. Não compara as outras frentes com uma versão antiga que pudesse apagar evoluções legítimas.

Artefatos de evidência:

- `rs-editorial-review`, ID `10656329195`, no run de validação. SHA-256 do ZIP: `25ed3fdc4549a8bbd6e5422e7a25cd113034f0026c57eb95559e2cedc502d754`.
- `rs-live-verification`, ID `10656598054`, no run público. SHA-256 do ZIP: `7e1660de86088fcd8d23112080a9e7e3cabf29fc354bc2c0dd3cf86409b43da1`.

O JSON de conferência pública contém caminho, status, tamanho, tipo de conteúdo, hash esperado e hash recebido por arquivo. A cópia da entrega também o acompanha. Os artefatos do Actions têm retenção de 14 dias; os relatórios de cobertura e testes estão versionados em `docs/rs/`.

## Pendências mantidas

A **issue #1 permanece aberta**. Faltam documentação suficiente para as 61 fichas sem síntese, pautas/atuação nas duas fichas apenas biográficas, reconciliação dos oito registros nominais e ampliação da conferência de cargos ainda não confirmados. As lacunas estão listadas por candidatura em `candidate-matrix.json` e `README.md`.

Foi entregue um procedimento manual reproduzível em `ATUALIZACAO-MANUAL.md`. Não foi instalada atualização recorrente. A conclusão técnica e a publicação desta rodada não equivalem à conclusão integral da pesquisa editorial.

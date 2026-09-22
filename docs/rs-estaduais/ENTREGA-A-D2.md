# RS-EST-AD2-CLOSE — fechamento de recuperação

**Fechamento técnico concluído; pesquisa editorial integral permanece aberta.**

## Recuperação e correção dos números

O commit `b73e18867d2d11c08a0c466fa3c55f3f15398184` e o artefato 10660708420 contêm 149 candidaturas, 61 sínteses e 395 linhas históricas com votos. As referências anteriores a 71 sínteses e 394 votos não foram reproduzidas. Não se presume a existência de dez sínteses locais ausentes do GitHub.

A configuração canônica contém onze siglas, incluindo PCB, PSTU e REDE. PCB e PCO têm zero registros neste snapshot; REDE e PSTU acrescentaram duas candidaturas cada na correção anterior. A configuração compartilhada foi somente lida.

## Resultado reproduzido

- 149 candidaturas representadas e conciliadas com o cadastro preservado.
- 61 sínteses; 88 fichas ainda sem síntese.
- 16 mandatos confirmados nas fontes datadas preservadas; 31 fichas com 44 atos documentados.
- 395 votos conferidos em 432 linhas históricas; 11 totais pendentes e 26 posições de vice/suplência sem voto nominal próprio.

## Estado individual da pesquisa

- Fontes consultadas: material insuficiente: 6.
- Síntese com fonte individual: 61.
- Pesquisa complementar pendente: 74.
- Leitura de fonte relevante bloqueada: 8.

Cada candidatura tem status, fontes, tentativas recuperadas e próximo passo. Pendência não virou pesquisa concluída nem ausência de propostas. Link bloqueado identifica dificuldade de acesso, não uma conclusão sobre a pessoa. As buscas nominais anteriores foram preservadas sem alegar exaustividade.

## Reprodutibilidade e testes

Duas reconstruções com rede bloqueada produziram os mesmos bytes nos arquivos comparados. 92 testes unitários passaram sem skips e 63 verificações de navegador passaram. A verificação com histórico Git foi executada no CI.

O controle de fontes registra disponibilidade e hashes sem transformar HTTP 200 em validação de conteúdo. Nenhum corpo integral de campanha ou dado de doador foi copiado para o relatório. As confirmações de mandato preservadas não foram redatadas como novas confirmações.

## Isolamento e GitHub

Mesma branch `feat/rs-deputados-estaduais`, issue #5 e PR #9. Sem merge, deploy ou encerramento da issue. Nenhuma modificação nesta execução à homepage, SC, RS/federais, navegação global, servidor, sitemap global ou configuração canônica.

## Próximos gates

E continua sendo a auditoria editorial independente da edição consolidada. F deve coletar novamente TSE/DivulgaCand, produzir o delta e decidir a liberação. A situação eleitoral mostrada pertence ao snapshot de 21/09/2026 às 12:31:37. O fechamento técnico de 22/09/2026 não atualiza silenciosamente esse dado.

## Arquivos

`recovery-audit.json`, `reproducibility.json`, `scope-reconciliation.json`, `source-availability.json`, `editorial-structure-audit.json`, `candidate-coverage.*`, `historical-vote-pendencies.*`, `isolation.json` e `report.json` documentam o fechamento. O export público de status está em `pesquisa-status.json`.

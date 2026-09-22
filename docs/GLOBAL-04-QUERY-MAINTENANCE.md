# Manutenção da consulta GLOBAL-04 / lote 02

## Pontos de edição

SC Estadual tem fonte em `deputados-estaduais/ui/app.js`, copiada para
`deputados-estaduais/assets/app.js` pelo seu renderer. RS Federal usa
`tools/rs/runtime.js`; PR usa `tools/pr/runtime.js`.

SC Federal e SP têm geradores históricos que sobrescrevem scripts finais. Suas
versões integradas ficam em `tools/global04/query_runtime/sc-federal.js` e
`sp-federal.js`. Depois de uma geração editorial autorizada, o refresh copia esses
scripts de integração e reaplica navegação, coleção e consulta. A correção de um
runtime SC/SP precisa ser feita nessa fonte versionada e no output correspondente;
o teste de manutenção exige paridade entre ambos. Os scripts leem os dados atuais
da edição; não contêm uma nova matriz de associações políticas.

## Comando após revisar conteúdo gerado

```bash
python tools/global03/refresh.py --edition 2026-sp-federais \
  --input sp/deputados-federais/index.html \
  --source-path sp/deputados-federais/index.html
python tools/global03/publication.py --prepare
```

O refresh não autoriza executar um pipeline de pesquisa antigo sobre uma revisão
mais nova. Em especial, scripts históricos que esperam SC Federal na raiz não
podem ser executados contra a home global. O caminho de input precisa corresponder
à saída editorial efetivamente revisada, com suas fontes e datas preservadas.

## Verificações

A suíte anterior executa reconstruções completas de SC Estadual, RS Federal e
PR (dois cargos), seguidas do refresh. `query_maintenance.py` acrescenta duas
simulações separadas: repõe o runtime pré-lote de SC Federal/SP num worktree e
executa o refresh real. Compara conteúdo de todas as fichas, JSON de pesquisa e
home; depois testa multipartido por IDs exatos, compartilhamento de consulta e
coleção no navegador. Isso testa manutenção dos scripts, **não uma nova geração
de pesquisa de SC/SP**.

Todos os workflows finais usam permissões de leitura. Os helpers
`finalize_query.py` e `polish_query.py` descrevem as migrações aplicadas durante o
desenvolvimento. Não são coletores nem tarefas agendadas. A issue #50 permanece
fora deste lote; o estado de consulta e as coleções continuam por edição.

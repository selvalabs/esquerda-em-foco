# GLOBAL-04 · lote 02 — consulta comum e controles compartilháveis

Issue #43, depois do lote 01 publicado pelo PR #49. Baseline deste lote:
`1a71c03987f52104af12af42eebda52449ff5570`.

## Escopo

O lote compõe a consulta existente nas seis edições sem substituir o significado
político dos dados. O contrato comum cobre busca, múltiplos partidos, critérios
locais já existentes, estado da consulta e compartilhamento explícito. A nova
seleção partidária usa **OU**: marcar PT e PSOL consulta registros de PT ou PSOL;
não produz pontuação, afinidade ou ordem de relevância.

A consulta nova permanece em memória. Só ao escolher “Compartilhar consulta” é
gerado um fragmento versionado `eef=query`, contendo eleição/UF/cargo e apenas
campos suportados pela edição. O site não salva esses critérios em conta,
localStorage, cookie ou backend. O link compartilhado não é secreto. PR e SP
continuam lendo URLs legadas; na primeira interação nova, a query antiga deixa de
ser usada como formato automático de persistência.

## O que cada edição conserva

- **SC Federal:** busca + multisseleção de partidos + filtros de `current_support`
  com Qualquer/Todas e motivo “Neste trecho”. Não converte atuação histórica em
  apoio atual.
- **SC Estadual:** busca + múltiplos partidos + situação do registro + trajetória
  já documentada. O controle existente continua distinguindo mandato confirmado,
  primeiro pleito no histórico e eleições anteriores.
- **RS Federal:** busca + múltiplos partidos. Não foram inventados filtros de
  mandato, situação ou pauta para campos ainda sem contrato equivalente.
- **PR Federal/Estadual:** busca + múltiplos partidos + situação + mandato +
  histórico + localidade documentada + temas legados. Os temas continuam em AND e
  `legacy_context`; este lote não os promove a apoio atual.
- **SP Federal:** multisseleção nativa + situação + `documented_topic` em
  Qualquer/Todos + ordem diária/alfabética. A extensão temática e os aliases já
  revisados permanecem próprios de SP.

Contagens são por fichas/pessoas distintas no universo da edição e não pelo número
de fontes ou afirmações. A ordem diária/alfabética continua independente da
quantidade de temas ou evidências.

## Preservação

Nenhuma associação candidato→tema é criada, removida ou copiada entre edições.
Textos, IDs, atributos cadastrais, fontes, snapshots e cards são comparados contra
a baseline. Selecionados do lote 01 continua separado por edição e precisa manter
a consulta ao entrar/sair do leitor.

Os runtimes dos renderers continuam sendo as fontes de manutenção. Depois de uma
geração antiga, `tools/global03/refresh.py` reaplica primeiro navegação/coleção e,
quando `global_query_v1` estiver habilitado, reaplica o contrato deste lote com
`query_build.py --no-metadata`. Não executar o bootstrap GLOBAL-02 contra a home.

## Gates

- contratos puros de fragmento, edição, modos e importadores PR/SP;
- multisseleção OR real nas seis edições;
- controles locais e semânticas preservados;
- compartilhamento explícito e reconstrução em navegador novo;
- link estrangeiro/critério inválido não destrói consulta atual;
- Selecionados continua funcionando e devolvendo a pessoa à consulta;
- noJS mantém todas as fichas legíveis e esconde apenas ferramentas interativas;
- 320–1440 px sem overflow nos ensaios;
- rebuild/refresh e segunda geração determinísticos;
- CI de liberação somente leitura antes de merge;
- conferência HTTP/SHA-256 e navegador depois da publicação.

## Não concluído por este lote

G4-D continua obrigatório: composição da ficha, evidência e transparência,
incluindo cadastro/mandato/histórico, natureza/período das afirmações, fontes e
estados de cobertura. O crosswalk entre taxonomias também exige revisão explícita.
RS/Estaduais segue com gates próprios. A issue #50 de caderno multi-edição está
estacionada e não faz parte deste lote.

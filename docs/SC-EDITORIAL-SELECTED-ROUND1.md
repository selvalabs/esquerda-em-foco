# SC/Federais — revisão editorial e coleção, Round 1

**Preparação em branch, sem alteração do site publicado.**

## Entrega

Revisadas as 48 fichas: 39 blocos documentados em 29 fichas e o aviso de lacuna em outras 19. Os 145 itens, 156 associações, 112 elegibilidades e 36 fontes permanecem vinculados ao material de origem. Não foi realizada nova pesquisa integral de candidaturas.

A camada pública agora é organizada em parágrafos com referências próprias. Pautas atuais e Outras posições permanecem separadas. O título escolhido para histórico é Atuação registrada, pois o bloco também contém iniciativas de 2026. As ressalvas que mudam a leitura permanecem junto do texto; o detalhamento fica em Fontes e contexto.

Cada parágrafo aponta para os itens exatos de origem. As 156 associações têm um localizador, permitindo reduzir a repetição do motivo dos filtros no Round 2 sem classificar o texto novamente. Um localizador não transforma todas as frases do parágrafo em justificativa de um mesmo tema.

## Selecionados: delimitação da entrega

O protótipo permite reunir fichas, removê-las, navegar na ordem de seleção e abrir uma ficha individual de cada vez. Não implementa o comparativo lado a lado ou as seções sincronizadas descritos no escopo inicial. Compartilhamento nativo, WhatsApp e cópia são preparados sem acesso a contatos ou envio automático.

A produção ainda não interpreta links de coleção. Por isso, no protótipo, a cópia de um link local de coleção é identificada como teste; envio da coleção para aplicativos externos fica desativado. O compartilhamento individual aponta para a âncora já existente no site.

## Arquivos

`data/sc-editorial-selected-r1/editorial.json`: camada pública e referências por parágrafo.

`parity-audit.json`: vínculo entre a redação revisada e os itens originais. `paragraph-locations.json`: localizadores das associações. `decisions.json`: escolhas editoriais. `manifest.json`: cobertura e isolamento.

`tools/sc_editorial_selected/`: entradas editoriais, compilação, núcleo de seleção e protótipo. A prévia HTML autocontida é gerada somente em `/tmp/eef-editorial-selected-r1/` e entregue como artifact, não publicada pelo Pages.

## Limites e próxima etapa

Testes de estrutura não certificam automaticamente a equivalência política das frases. A revisão de redação foi feita sobre os itens aprovados; fontes, datas, natureza e elegibilidade originais foram mantidas. Falta de fonte suficiente não foi preenchida com suposições.

O Round 2 integra a camada pública à listagem existente, conecta Selecionados à navegação sem alterar os filtros e habilita os links de coleção no endereço publicado. Exige QA do merge efetivo, revisão visual e teste do compartilhamento real nos aplicativos disponíveis. Nenhuma comparação, avaliação ou recomendação entre candidaturas faz parte da implementação.

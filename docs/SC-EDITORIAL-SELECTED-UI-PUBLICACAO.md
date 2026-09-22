# SC/Federais — redação editorial e Selecionados publicados

**Issue #36, Round 2 concluído em 22/09/2026.** A redação revisada e a coleção de consulta individual foram integradas pelo PR #38 e verificadas no GitHub Pages. Não é mais apenas o protótipo do Round 1.

Site: https://selvalabs.github.io/esquerda-em-foco/

## Integração

- PR #38: https://github.com/selvalabs/esquerda-em-foco/pull/38
- Commit integrado: `979332c01df2155ab49133a9cfeca83664917e52`.
- Base efetiva preservada: `d8bf0ae43a24f0f8f297316bb366e497dc3dfc8c`.
- Branch: `feat/sc-editorial-selected-round2`.
- Head aprovado: `60d6ab5bf77950ad7b27364a796eb89b4499b678`.
- Merge candidato testado: `97a120ae320f65079928485bb7d73955a91654d4`.

A preparação do PR #37 foi incorporada por esse histórico. O GitHub marcou o #37 como merged junto com a integração; não houve publicação isolada do protótipo como funcionalidade pronta.

## O que está no site

As **48 fichas** agora usam a redação aprovada: **67 parágrafos** nos blocos documentados e avisos claros nos casos de documentação insuficiente. Os títulos são **Pautas atuais**, **Outras posições**, **Atuação registrada** e **Fontes e contexto**. As referências aparecem junto dos parágrafos, de forma legível e com repetições compactas. Ressalvas essenciais continuam próximas do texto; as limitações originais foram preservadas.

O motivo dos filtros deixou de repetir um bloco extenso visível inicialmente. As indicações **Neste trecho** ficam recolhidas junto ao parágrafo relevante e abrem o registro específico com sua fonte. O vínculo usa IDs aprovados, não palavras-chave. Não se presume que todas as afirmações do parágrafo tratem do mesmo tema.

Cada ficha possui **Selecionar/Selecionado** e **Compartilhar ficha**. A navbar traz o atalho e a contagem de Selecionados. Quando há itens, uma barra acima do rodapé também permite abrir a coleção.

A coleção aceita de uma a todas as 48 fichas, na ordem em que foram selecionadas. Abre **uma ficha por vez**, com Anterior/Próxima, remoção, limpeza com confirmação e retorno à lista. Não há comparação lado a lado, seções sincronizadas, pontuação ou recomendação entre candidaturas.

A busca e os filtros não apagam a coleção. Uma ficha temporariamente oculta por eles continua disponível em Selecionados. O leitor usa o próprio elemento da ficha, sem copiar dados ou duplicar IDs; ao fechar, ele volta ao marcador original, e os critérios e a rolagem da listagem são restaurados.

## Compartilhamento

A opção Compartilhar ficha gera o link da âncora individual. **Compartilhar selecionados** gera um link que reconstrói o conjunto, sua ordem e a ficha aberta. A reconstrução foi confirmada no site público com um novo contexto de navegador, simulando quem recebe o link.

O diálogo oferece **Copiar link**, **WhatsApp** e **Outros aplicativos** quando o compartilhamento nativo estiver disponível. A pessoa escolhe o contato e confirma o envio no aplicativo. Nenhum contato é lido e nenhuma mensagem é enviada automaticamente pelo site.

A cópia só informa sucesso quando confirmada pela API; em caso de falha, o endereço fica disponível para seleção manual. Cancelar o compartilhamento nativo não aciona outro canal. A confirmação nativa indica entrega ao compartilhador, não que um contato recebeu a mensagem.

**A coleção não é salva no navegador.** Ao recarregar, ela só é reconstruída quando o link contém os itens. As escolhas não entram em cookies, armazenamento local, backend ou métricas. O link não é secreto: qualquer pessoa ou aplicativo que o receba poderá ler os itens incluídos. Ele conserva IDs e ordem, não uma cópia histórica dos textos.

## Conteúdo e demais frentes preservados

A implementação não fez nova pesquisa, não alterou os fatos documentados nem reclassificou pautas. O recorte continua datado de **21/09/2026**. Os **145 itens**, as **156 associações**, as **112 elegibilidades v2** e as **36 fontes** permanecem vinculados à base aprovada. As lacunas documentais anteriores não foram preenchidas por inferência.

Os cabeçalhos, as redes, as fotos, os dados eleitorais e as trajetórias das fichas foram preservados. A rotação diária permanece responsável pela ordem da listagem. As outras edições e frentes não receberam os controles de Selecionados nesta entrega.

A navbar mantém os links e o hambúrguer mobile. O layout intermediário de tablet foi acomodado em duas linhas para evitar colisão com o novo atalho. Os diálogos receberam posicionamento fixo para manter cabeçalho e retorno visíveis ao navegar às fontes.

## Validação de preparação e merge

Preparação aprovada: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35732576691

Merge candidato aprovado: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35733140064

As duas etapas aprovaram **580 verificações principais e 118 regressões adicionais**, sem falhas. A execução dos **12 testes Node** está incluída na primeira contagem; não deve ser somada outra vez.

A validação contra a base efetiva confirmou **1.603 arquivos preexistentes fora das áreas autorizadas preservados byte a byte**, além das proteções internas do index. A compilação é determinística.

Chromium em **320, 360, 390, 430, 768, 1024 e 1440 px**. Os ensaios cobriram seleção de 0 a 48 fichas, remoção da ficha aberta, limpeza, busca, OR/AND, estado vazio, retorno, links, foco, cancelamento, entradas inválidas, falhas de assets, ausência de JavaScript e rotação diária. A regressão também verificou o acesso real ao botão da navbar, a permanência do diálogo dentro do viewport e a separação entre barra e rodapé.

Capturas finais de leitura em 320/390/1440 px, compartilhamento em 320 px e navbar em 768 px foram inspecionadas. Fontes e imagens externas foram bloqueadas nos testes. Não se afirma ensaio em aparelho físico, leitor de tela real ou inspeção individual de todas as fotografias.

Artifact do merge: **10696471744**, `sc-selected-ui-merge`.
SHA-256 do ZIP: `8ca9fc8c39f3fb4befdf599889ba30446d565137b28691baf77b05e10c2a56fc`.

As tentativas anteriores que falharam não foram publicadas nem contadas como sucesso. Os ajustes de layout e do próprio teste estão registrados em `docs/SC-EDITORIAL-SELECTED-UI-VALIDACAO.md`.

## Prova da publicação efetiva

Run: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35733459220

Job `verify-published`: **106764581454**, concluído com sucesso.

Conferência registrada em **2026-09-22T13:28:29.007245Z**. Os **12/12 arquivos** responderam HTTP 200 e coincidiram em SHA-256 com o commit integrado.

No site público, o navegador abriu as larguras **390 e 1440 px**, encontrou 48 fichas e 67 parágrafos, reuniu duas fichas, navegou às fontes e à ficha sem pauta filtrável, preparou o link e conferiu o formato do WhatsApp. Depois abriu o link da coleção em um novo contexto, confirmando IDs, ordem e ficha ativa. Ao retornar à listagem, o filtro permaneceu aplicado. Não houve erros JavaScript, overflow horizontal ou entradas em armazenamento local nesses ensaios.

Nenhuma mensagem foi enviada no WhatsApp. Os testes de cancelamento, clipboard e Web Share da preparação foram simulados; a verificação pública confirmou a construção do link e sua abertura no site, não a entrega por um aplicativo externo.

Artifact público: **10696083470**, `sc-selected-ui-live`, com relatório e capturas.
SHA-256 do ZIP: `23da56a37481bde3c3493c66f5372aacce8d34cca518c09dec9096aec124e5a7`.

| Arquivo | SHA-256 publicado |
|---|---|
| `index.html` | `0131074ef3758f72ba592e5c1e19703c013baa95d34363700ead92b8c627ee38` |
| `assets/editorial-selected.css` | `f9e744fa74b24aa614e11e22e3d5f1ee97f65469584641862469ad8596291d5c` |
| `assets/selecionados.js` | `25804fb895beecca3c01b2e2cb6c50e5a88aa1b53161ed6840c5a6c0ca53a27e` |
| `assets/selecionados-core.js` | `80ed2a10496a8a1f5684d61b9e26d80a5ad2e105f1d37189f8a43f31bbd46bb5` |
| `assets/pauta-filters-editorial.js` | `1c92d36c64a86c56d4bc68048796ae54cc12ccbb68abbb7c938d70d70f08c3e8` |
| `assets/pauta-filter-core.js` | `6ce62d78351d460e49494f1c47f6164b26e139b6df7e56b9fc990cf7fcc50afd` |
| `assets/pauta-filters.css` | `481fbd4867c858858b0b76341f9c551c8ffaa4877408e6db6bbb5189347c439a` |
| `assets/pauta-v2.css` | `95309a77adc7f31657f9c214de7b3cd6c624fdf4b01072b0a1185e2b78f1d06c` |
| `assets/sc-federais-filters-v2-data.js` | `0a2ac880d0f82b6a7ed7e89066a7e52c1a46e52e698d519550213c9ad5adcc86` |
| `data/sc-selected-ui/manifest.json` | `4ae5c59d483a3c2a71d91cc034cf688890ce8efabbea5427ffbd1e05e10110ea` |
| `data/sc-editorial-selected-r1/editorial.json` | `003a12f777dae2cf04d9e560f39c78a7be1e00e485b78e34e6cd97642cbfa19a` |
| `data/sc-semantic-v2-ui/payload.json` | `ac3b31e47daf45b090fff9f5a7e25a20eaf03f40f14a03836b4857d784841f2b` |

## Fechamento

Os dois rounds da #36 estão integrados e publicados no escopo ajustado de redação e coleção para consulta individual. O comparativo lado a lado e as seções sincronizadas entre candidaturas não foram implementados.

Arquitetura: `docs/SC-EDITORIAL-SELECTED-UI.md`. Contrato: `docs/SC-EDITORIAL-SELECTED-CONTRACT.md`. Dados da integração: `data/sc-selected-ui/`. Os relatórios do Round 1 permanecem como proveniência, não como descrição do estado público atual.

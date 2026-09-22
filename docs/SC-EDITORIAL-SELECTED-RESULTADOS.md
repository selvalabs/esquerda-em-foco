# Issue #36 — resultados do Round 1

Data: 22/09/2026. Branch: `feat/sc-editorial-selected-round1`. Baseline: `d8bf0ae43a24f0f8f297316bb366e497dc3dfc8c`.

**A revisão editorial, o contrato técnico e o protótipo isolado estão preparados. Esta entrega não altera o site publicado.** A integração da interface pertence ao Round 2. A implementação não inclui o comparativo entre candidaturas previsto inicialmente: Selecionados é uma coleção para abrir e compartilhar fichas individuais, uma por vez.

## Revisão editorial

Foram tratadas as 48 fichas: 39 blocos documentados em 29 candidaturas e o aviso de lacuna nas outras 19. A nova redação organiza o conteúdo em 67 parágrafos, com referências ligadas aos itens que os sustentam. Todos os 145 itens, 156 associações, 112 elegibilidades v2 e 36 registros de fontes mantêm seus vínculos. Não foi feita nova pesquisa integral das fontes nem das candidaturas com documentação insuficiente.

Os títulos públicos propostos são **Pautas atuais**, **Outras posições**, **Atuação registrada** e **Fontes e contexto**. Atuação registrada foi escolhido em lugar de Atuação anterior porque o bloco também descreve iniciativas de 2026 e eventos sem data exata. O conteúdo não recebe uma antiguidade inventada para caber no título.

A linguagem foi reorganizada para reduzir enumerações longas e repetir menos uma mesma abertura. As ressalvas que mudam o sentido continuam próximas do texto: autoria atribuída, fonte não reconfirmada, data indeterminada e relato de voto não verificado. Explicações de procedimento ficam em Fontes e contexto, sem apagar as limitações originais.

As fontes ganham rótulos legíveis por parágrafo, com tipo de material e data original quando confirmada. A data da consulta não é usada como data da publicação. A apresentação final desses rótulos ainda poderá ser ajustada na integração para reduzir repetição quando vários parágrafos compartilham a mesma fonte, sem perder o vínculo individual.

`paragraph-locations.json` prepara a redução de duplicações do motivo dos filtros. Cada associação aponta para um parágrafo e conserva sua evidência específica. Isso é um localizador, não uma autorização para tratar todas as afirmações do parágrafo como apoio a uma mesma área. A aplicação desse destaque à listagem existente fica para o Round 2.

## Selecionados: o que o protótipo faz

Permite selecionar de uma a todas as 48 fichas, sem limite artificial de três ou quatro. A coleção segue a ordem de seleção, sem usar pautas, votos, experiência ou quantidade de fontes. Remoção e reinserção são explícitas, e a busca de nomes não apaga os itens escolhidos.

A leitura mostra uma ficha por vez. Anterior e Próxima percorrem a coleção; a remoção da ficha aberta leva a outra existente ou ao estado vazio. Não há exposição comparativa lado a lado, seções sincronizadas, identificação de diferenças, classificação ou recomendação.

O núcleo prepara links versionados com edição, IDs e ficha aberta. Ele valida os IDs do catálogo, remove duplicatas, trata links incompletos ou inválidos sem sobrescrever uma coleção válida e mantém as âncoras individuais antigas distintas do novo formato.

As escolhas ficam somente em memória e não são salvas no navegador nem enviadas à API de métricas. Um link compartilhado pode ser lido por seus destinatários e pelo aplicativo escolhido; ele não é secreto ou criptografado pela aplicação. O link reproduz o conjunto e a ordem, não uma cópia histórica do conteúdo.

## Compartilhamento e limites da prévia

O link individual aponta para a ficha já existente no site. O protótipo oferece preparação para WhatsApp, compartilhamento nativo quando disponível e cópia do endereço. A pessoa escolhe o destinatário e confirma o envio no aplicativo. Nenhum contato é acessado e nenhuma mensagem é enviada automaticamente.

Como o site publicado ainda não entende links de coleção, o compartilhamento externo da coleção fica desativado na prévia. Sob HTTP local, o link da coleção pode ser copiado e reaberto para teste, com aviso explícito de que não é um recurso publicado. Abrindo apenas o arquivo HTML, leitura e seleção funcionam; a construção de links locais exige um servidor HTTP.

Cancelar o compartilhamento não tenta outro canal. A confirmação da API nativa significa entrega ao compartilhador do aparelho, não recebimento por um contato. A cópia só anuncia sucesso depois da confirmação; falhas deixam o link selecionável para cópia manual.

## Validação da preparação

Run aprovado: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35728809017

Código testado: `63ceeebf0cef70e0ccd5c2b0cd29c6fd827bbc4c`.

**469 verificações aprovadas, zero falhas**, incluindo a execução dos **12 testes Node**, todos aprovados. Essa suíte está incluída na contagem de verificações; os números não devem ser somados como 481 verificações independentes.

Foram preservados byte a byte **1.604 arquivos preexistentes**, incluindo index, assets, dados eleitorais, fontes, taxonomias e as outras frentes do projeto. A compilação de dados, relatório e prévia foi repetida com resultado idêntico.

O navegador Chromium foi exercitado em **320, 360, 390, 430, 768, 1024 e 1440 px**, com seleção, navegação individual, remoção, limpeza com confirmação, busca de nomes, reconstrução de coleção, links inválidos, foco de diálogos, cancelamento, cópia manual e alteração de largura. O gesto horizontal foi simulado; isso não é um ensaio de uso em aparelho físico.

Web Share e clipboard foram simulados. As URLs do WhatsApp foram conferidas, mas nenhuma mensagem foi enviada. Não houve teste em aplicativo externo, leitor de tela real ou validação da integração com os filtros do site, que ainda não foi feita. O teste sem JavaScript verifica a orientação da prévia; o site publicado permanece inalterado.

Foram inspecionadas visualmente as capturas de leitura individual em **320, 390 e 1440 px** e do diálogo de coleção em **320 px**. Elas mostram a hierarquia de leitura, fontes, ressalvas e ausência de comparação entre candidaturas. Não se afirma inspeção visual individual de todas as 48 fichas.

A primeira tentativa de QA parou numa comparação entre texto de título e a capitalização aplicada pelo CSS. A checagem passou a comparar o conteúdo do título separadamente de sua apresentação. Os cenários independentes de navegação também passaram a abrir um documento novo em vez de depender apenas de troca do fragmento. A execução aprovada substitui aquela tentativa; não houve publicação da tentativa que falhou.

Artifact aprovado: **10693873984**, `sc-editorial-selected-round1`.
SHA-256 do ZIP: `212b0d66c6f895743fbe6d5219eefe6a0cbf9d0f07b7004c287f958a2778eb62`.

Testes de estrutura e de links não certificam automaticamente equivalência de sentido político. A redação foi revista sobre os itens documentados; a base factual permanece preservada, sem novas associações inferidas.

## Continuidade

A branch deve seguir para PR de revisão, sem publicação nesta rodada. A issue #36 permanece aberta. O Round 2 integrará a camada editorial aos cards reais, conectará Selecionados à navegação existente e habilitará os links públicos de coleção, com novo QA do merge efetivo e da publicação.

Contrato: `docs/SC-EDITORIAL-SELECTED-CONTRACT.md`.
Relatório gerado: `docs/SC-EDITORIAL-SELECTED-ROUND1.md`.
Dados: `data/sc-editorial-selected-r1/`.
Protótipo gerado: artifact, em `tmp/eef-editorial-selected-r1/index.html`.

O comparativo entre candidaturas e as seções sincronizadas não foram executados e não são registrados como concluídos.

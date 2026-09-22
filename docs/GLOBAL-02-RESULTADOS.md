# GLOBAL-02 · resultado da implementação e gates de liberação

Issue #41, PR #46, epic #39. Data: 22/09/2026.

## Entrega

A fundação implementa catálogo, identidade por eleição/estado/cargo, disponibilidade
real de recursos, templates independentes, contratos de consulta/evidência/coleção
e navegação compartilhada. A home pública continua sendo a edição SC/Federais.
O novo shell, os destinos SC e os hubs foram exercitados num ensaio isolado;
não são apresentados como publicados. A #42 recebeu o handoff de ativação.

## Validação concluída da implementação

Baseline: `cb845fcfb0b57f7907fd9d129555b6bb558a9ce1`.
Commit efetivamente executado: `d06193c5e63629f46196d14611907cdd934a35ce`.
RS Estadual, somente leitura: `c2bfa3ece357f21e8aa09e32f624a9e214ad9113`.

Execução: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35754792204

| Conjunto | Resultado |
|---|---|
| Contratos novos de rotas, consultas e coleções | 34 testes aprovados, zero falhas/skips |
| Lógica preexistente SC/SP | 47 testes aprovados, zero falhas/skips |
| Preservação e reconstruções reais | 1.691 verificações aprovadas; inclui hashes de 1.644 arquivos preexistentes |
| Catálogo, adapters e navegador | 392 verificações aprovadas; adapters sobre 909 registros |
| Segunda preparação | Sem diferença de arquivos; árvore de trabalho limpa |

As 1.691 verificações não são todas testes de funcionalidades: a maioria verifica
preservação de arquivos. As 392 incluem validação de dados/contratos além de
interações de navegador. Reexecuções de liberação não devem ser somadas a esses
números como se fossem testes independentes.

Artefato `10708080087`, SHA-256
`b544870a69fa5f9bf990e18490d803d6e76d7d1bedff7dd4ff78eac911bd0d62`.
Os relatórios originais e seus hashes são localizados em `data/global02/qa.json`.
A confirmação de integração, SHA final e reexecução de liberação ficam no PR #46
e na issue #41, sem redatar os resultados deste commit de implementação.

## O que a reconstrução demonstrou

SC Estadual usa seu template versionado e preservou identidade e texto das 97
fichas. RS Federal preservou as 111; PR preservou as 115 federais e 140 estaduais.
Após substituir a raiz por um arquivo sem cards e, quando pertinente, retirar o
HTML pronto de RS Federal, os outputs selecionados mantiveram os mesmos bytes.
Os comandos e caminhos comparados constam de `tests/global02/rebuild.py`.

RS Estadual foi reconstruído pelo pipeline incremental AD3, em worktree descartável.
Dados, estados de pesquisa e correções preservaram os bytes; as 149 fichas, 72
sínteses e lacunas restantes não foram sobrescritas pelo pipeline histórico.
O patch para seu gerador é entregue separadamente. A branch não foi publicada,
atualizada ou incorporada ao main por esta tarefa.

## Navegação e transporte

Seis edições foram ensaiadas em 320/360/390/430/768/1024/1440 pixels, nos mounts
`/` e `/esquerda-em-foco/`. Sem overflow ou erros JavaScript nos ensaios. Houve
checagem de IDs únicos, menu nativo, Escape/foco, fonte SC via âncora, alias
estadual, 404, fallback sem JavaScript e reconstrução de coleção SC v1 com a ficha
ativa preservada. As 12 capturas mobile/desktop coincidiram byte a byte com o
ensaio anterior; as seis mobile e os detalhes de SC mobile/SP desktop foram
inspecionados visualmente.

Coleções foram testadas com 48, 97, 149, 249, 513 e 3.000 IDs. Uma seleção de
5.000 permanece íntegra em memória, mas o transporte que supera 65.536 caracteres
é recusado sem truncamento. O novo núcleo não foi ligado automaticamente aos
leitores das outras edições; essa integração é a #43.

## Preservação e datas

Nenhum HTML público ou export eleitoral/editorial preexistente foi modificado.
Os únicos cinco arquivos antigos alterados são quatro pontos de entrada dos
geradores e o sitemap. O sitemap corrente enumera oito destinos já publicados;
as onze rotas futuras estão separadas, sem publicar uma branch como edição.

O catálogo copia datas e proveniência dos datasets, não transforma a data desta
tarefa numa nova consulta TSE. Para SC Federal, a data agregada não normalizada
permanece nula e acompanhada de limitação: as referências originais continuam no
HTML. Apoio atual, tema documentado e contexto legado mantêm semânticas distintas.
Os catálogos locais 29/30/28/25 e os aliases SP declarados foram preservados, sem
criar equivalências ou associações novas por palavra-chave.

## Falhas intermediárias e correções

A primeira tentativa não encontrou Pillow no ambiente de reconstrução SC.
Depois foi identificado o parser XML ausente no renderer RS. As dependências
foram adicionadas explicitamente ao ambiente; não foram relaxadas as verificações
de conteúdo ou preservação para conseguir aprovação. Tentativas falhas permanecem
registradas. A suíte de navegador foi independente da reconstrução nas tentativas
posteriores e produziu seus próprios resultados, sem converter falha global em
sucesso. O workflow final fica com `contents: read`, sem commit ou push automático.

## Handoff da home e limites

A #42 deve construir a home/hubs de verdade, ativar destinos e catálogo no mesmo
commit, revisar todos os atalhos locais entre edições, ajustar canonical/OG/JSON-LD
e remover `noindex`/robots bloqueado do pacote de produção. O ensaio conserva os
menus locais existentes e não é um pacote pronto para deploy. Links antigos só à
raiz, sem fragmento, não permitem distinguir uma intenção de abrir SC de uma
visita nova à home; acesso explícito a SC é obrigatório na home.

Não houve nova coleta TSE, revisão externa das posições políticas, conferência
HTTP pública, aparelho físico, leitor de tela real ou envio de WhatsApp. A falha
local SP de ficha oculta após busca e mudança de hash permanece na #43/#44.
Integração técnica não encerra pesquisas editoriais independentes.

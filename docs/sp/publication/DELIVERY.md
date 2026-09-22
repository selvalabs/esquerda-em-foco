# São Paulo — integração e publicação verificadas

**22/09/2026. PR #31 integrado. GitHub Pages publicado. Verificação do site público: PASS.**

Edição pública: https://selvalabs.github.io/esquerda-em-foco/sp/deputados-federais/

A tarefa autorizada foi revisar a integração do Round C sobre a main atual, preservar outras frentes, integrar o PR e verificar a publicação efetiva. Não foi uma nova rodada de pesquisa política ou eleitoral.

## Integração sem sobrescrever outras frentes

- Main anterior à integração: `85098ad9f8fe1ec8c5e4eff4ef1c2b0a9eaa3c52`.
- Head testado de SP: `2a0df48b2aec1294a2ce68178f5d93acd098af57`.
- Merge real do PR #31: `5fba8ef2375e65e3bca5298bd397c3dfb401e9e1`, em 22/09/2026 às 10:44:26 UTC.
- Árvore integrada: `71e7092dfcdffba5e66ec6abc77ccaf5848dcb69`.

A árvore do merge real é idêntica à árvore da simulação testada. Foram comparados **970 arquivos preexistentes**, todos idênticos à main de referência, excetuados os dois arquivos com mudanças intencionais: a home recebeu somente o link delimitado de SP; o sitemap recebeu somente duas entradas novas. Os dados e interfaces anteriores de SC/RS/PR não foram substituídos pelo snapshot da branch.

## Validação antes do merge

[Execução 35717415039](https://github.com/selvalabs/esquerda-em-foco/actions/runs/35717415039): concluída com sucesso.

| Verificação | Resultado |
|---|---:|
| SP — dados, HTML e reconstrução | 25/25 |
| SP — JavaScript e filtros | 16/16 |
| SC — interface semântica v2 | 9/9 |
| Recorte partidário canônico | 3/3 |
| RS — suíte existente | 51/51 |
| SP e navegação entre edições — Chromium | 23/23 |
| PR — suíte existente, na main isolada e no merge simulado | 19/20 em ambas |

O único teste não aprovado é `test_base.ParanáBase.test_15_sc_rs_unchanged`. Ele também falha na main isolada, sem SP, porque seu inventário histórico antecede alterações legítimas posteriores de SC/RS. A falha foi registrada, não ignorada, não convertida em skip e não contabilizada como PASS. A comparação independente com a main atual não encontrou nova regressão. A atualização desse teste legado permanece uma pendência de manutenção separada.

O rebuild de SP não mudou as saídas versionadas. Os cenários de navegador incluíram filtros, URLs compartilháveis, mobile, teclado, leitura sem JavaScript e navegação entre as edições disponíveis.

Artefato de preflight: `10690472417`; SHA-256 do ZIP baixado e inspecionado:

`fe0a411b69e42e888d4dbfe37b834430bcbff1df023f02de8b00e435c07e6728`

O artefato contém preflight.json, logs de cada suíte, comparação da navegação, browser-tests.json e capturas. Os testes HTTP foram executados no runner; as saídas e os hashes foram conferidos localmente após o download.

## Publicação efetiva e verificação no endereço público

O [Pages build and deployment 35717637258](https://github.com/selvalabs/esquerda-em-foco/actions/runs/35717637258) publicou o merge `5fba8ef`. A primeira checagem pública, [35717640043](https://github.com/selvalabs/esquerda-em-foco/actions/runs/35717640043), passou tanto em SP quanto em SC.

Foi corrigido apenas o caminho usado para incluir o relatório de SC no artefato (`70ce78b4f446daca4b7d7b7cf25034c250754d2a`). Essa correção não alterou HTML, CSS, JavaScript, dados ou as verificações. O Pages [35717861501](https://github.com/selvalabs/esquerda-em-foco/actions/runs/35717861501) e a checagem final [35717862561](https://github.com/selvalabs/esquerda-em-foco/actions/runs/35717862561) terminaram com sucesso.

A verificação final de SP ocorreu entre **10:47:25 e 10:47:41 UTC de 22/09/2026** e confirmou:

- **273 arquivos públicos** com HTTP 200 e SHA-256 idêntico ao checkout do commit verificado; incluem os arquivos da edição SP e páginas/recursos compartilhados selecionados.
- **12 grupos de cenários no navegador**, todos aprovados, em desktop de 1440 pixels e celular de 390 pixels, além da leitura sem JavaScript.
- **249 registros e 249 retratos carregados**, sem falhas de recursos locais ou erros JavaScript nos cenários de SP.
- Combinação de partido e tema, busca por número, recarregamento da URL e abertura da evidência documental.
- Contagens PSTU 5, REDE 10 e PCB 0, sem atribuição de temas aos registros adicionais não pesquisados.
- Link da home atual de SC levando à edição de SP e ausência de vazamento horizontal nos cenários.

O relatório de SC, registrado às **10:47:42 UTC**, também passou: **11 arquivos verificados**, 48 fichas, 13 botões de temas amplos e testes em 390/1440 pixels. A busca combinada, o texto de tributação e a separação de histórico em relação a apoio atual foram preservados, sem erros JavaScript ou overflow.

Artefato final de publicação: `10689482335`; SHA-256 do ZIP baixado, aberto e conferido:

`3b7d95394cfeb15c416d3e22610777da9b6ef37554e84667f03698a5c2a38a96`

Ele contém `sp-publication-live/publication.json`, quatro capturas de SP e `sc-semantic-v2-ui-live/report.json` com as capturas de SC. O inventário completo dos 273 hashes está no relatório de SP. A publicação foi confirmada pelo conteúdo e comportamento do endereço público, não apenas pelo status do build.

## Conteúdo publicado e limites preservados

A edição mantém os **249 registros**, as 30 famílias documentais e a camada herdada do Round C: 42 fichas com temas de 2026, 218 associações candidato–tema e 102 afirmações do período. Histórico e material sem data continuam separados dos filtros atuais. Nenhuma pesquisa de outra pessoa ou legenda foi copiada para suprir lacunas.

Os **15 registros adicionados da REDE/PSTU continuam sem pesquisa temática individual**. As falhas de disponibilidade anteriormente identificadas em 14 das 75 URLs editoriais continuam sinalizadas. Não foram visitados novamente todos esses links nem todos os perfis sociais. As lacunas biográficas, de cargos atuais e de votos históricos não foram consideradas resolvidas por esta publicação.

A checagem confirma integração, integridade dos arquivos publicados e funcionamento da interface. Não é prova independente da veracidade de todas as afirmações políticas herdadas, nem garantia de atualização eleitoral em tempo real. Registros sem tema documentado não representam oposição ao tema.

## Rastreabilidade e manutenção

- PR de implementação/publicação: #31, mergeado na main.
- Issue de execução: #25.
- Verificação pré-merge: `tools/sp/publication/preflight.py`.
- Verificação pública: `tools/sp/publication/verify_live.py`.
- Workflow de verificação: `.github/workflows/sp-publication.yml`.
- Entrega anterior da interface: `docs/sp/round-c/DELIVERY.md` (registro histórico pré-publicação).

Este documento foi acrescentado após os testes e não altera os arquivos públicos da edição. A interface está publicada; aprofundamento editorial e manutenção do teste legado de PR são frentes distintas desta entrega.

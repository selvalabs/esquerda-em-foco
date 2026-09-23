# GLOBAL-05 — revisão técnica e candidato de correção

**Issue #44; epic #39. Estado: candidato local, não integrado nem publicado.**

A revisão parte de `4a3300005fafbf85e13c4a61e763db1496924348`, encerramento funcional da GLOBAL-04. O conector disponível nesta sessão permite leitura, mas não criação de branches, comentários, commits ou PRs. Portanto, este documento não declara qualquer mudança no GitHub, conclusão da #44 ou fechamento do epic. A #50 permanece estacionada.

## Origem da versão examinada

A versão pública foi obtida do artefato `github-pages` 10744220549, run 35847844661, associado ao commit acima. O SHA-256 do ZIP recebido é `c0feee04e7a99b885746ae7a5771ada31384643feb42b69bc0ece0eae2cadcce`.

Os arquivos foram confrontados com o manifesto de publicação da versão-base. A cópia de trabalho também contém as fontes de geração das etapas anteriores. Nenhum hash histórico D1/D23/D5 foi regravado para aprovar esta modificação.

## Defeitos reproduzidos e correções

| Código | Problema observado na versão-base | Correção do candidato |
|---|---|---|
| G5-01 | Em SP, o botão do menu mobile anunciava abertura, mas os links continuavam ocultos. | A regra CSS reconhece `#siteNav.is-open .main-links`, sem remover a compatibilidade anterior. O botão atualiza seu nome acessível ao abrir/fechar. |
| G5-02 | Dentro de Selecionados, “Origem e limites” não abria o detalhamento nem conduzia o foco ao destino. | O resolvedor de âncoras reconhece o leitor aberto, expande os detalhes e leva foco/rolagem ao seu resumo, abaixo do cabeçalho. Não redefine os filtros nem desloca a página atrás do diálogo. |
| G5-03 | Remover um filtro ativo substituía o botão e deixava o foco no corpo da página. | O foco segue para o próximo filtro disponível ou retorna à busca, tornando-a visível quando a lista fica vazia. |
| G5-04 | A edição SP não declarava imagem Open Graph. | O finalizador reutiliza a imagem pública do projeto e acrescenta os metadados ausentes. Não altera a imagem existente das demais páginas. |

O finalizador `tools/global05/build.py` é chamado por `tools/global03/publication.py --prepare`, depois da geração editorial. Ele mantém as referências de CSS/JS alinhadas ao conteúdo dos arquivos e acrescenta apenas metadados ausentes. Não reserializa as fichas. Novas tags são inseridas antes dos assets regeneráveis, com serialização estável.

## Cobertura executada localmente

A suíte estática verifica as 13 páginas públicas: home, quatro hubs, seis edições, alias estadual antigo e corpo da página 404. Verifica títulos e descrições, canonical, robots por página, imagem de compartilhamento, manifesto, sitemap, rótulos de controles, referências ARIA, IDs e destinos locais. Os 11 endereços indexáveis são comparados ao catálogo; o alias é não indexável e aponta à edição canônica. A página 404 é não indexável e intencionalmente não possui canonical próprio.

A preservação compara a marcação de todas as 760 fichas e o payload `cqData` com a versão-base. Textos, fontes, identificadores, associações, snapshots e catálogos de pesquisa não são editados. A comparação de arquivos fora do escopo também é obrigatória.

A suíte de interação usa Chromium em 320, 360, 390, 430, 768, 1024 e 1440 pixels. Abrange menus, Escape, foco, leitura da própria ficha no diálogo, âncoras de origem, manutenção da consulta, remoção de filtros, confirmação de limpeza e leitura sem JavaScript. Há ensaios auxiliares de home/hubs e amostragem de contraste.

**Nesta sessão, esses ensaios de navegador são fixtures offline**, renderizadas com `page.set_content` e CSS/JS locais. A política do ambiente bloqueia navegações HTTP e `file://`; ela não foi alterada. O ensaio preserva a execução adiada dos scripts `defer`, mantém imagens locais e substitui imagens remotas por um placeholder. Os resultados não são uma verificação de rede, de carregamento do GitHub Pages ou de destinos externos. Nas fixtures de home e alias, o script `legacy-bridge.js` é omitido explicitamente: ele exige uma URL HTTP real para calcular o redirecionamento. O funcionamento dessa ponte não recebe aprovação pelo ensaio offline.

Nos diálogos nativos, Chromium pode transferir Tab à interface do próprio navegador. O teste não confunde essa saída do documento com foco na página inerte atrás do diálogo; quando o documento recupera foco, exige retorno ao leitor. Isso não é teste com leitor de tela.

## Contraste e interpretação dos resultados

A amostragem calcula contraste de texto visível em componentes selecionados sobre fundos sólidos: filtros, navegação e contexto das fichas. Aplica 4,5:1 ao texto normal e 3:1 ao texto grande, excluindo controles desabilitados. Não cobre exaustivamente texto sobre imagens/gradientes, estados de hover, todos os indicadores de foco ou controles gráficos.

Uma aprovação nessas amostras **não constitui certificação integral WCAG**, auditoria com leitor de tela ou teste em aparelho físico. Os relatórios JSON guardam os elementos amostrados, ratios e limites.

## Execução reproduzível

Dependências da validação: Python, Beautiful Soup, Playwright e Node. O workflow proposto fixa versões para CI. Os comandos abaixo são executados na raiz de uma cópia do repositório, com uma cópia imutável da versão-base em outro diretório:

```bash
python tools/global03/publication.py --prepare
python -m unittest discover -s tests/global05 -p 'test_*.py' -v
python tests/global05/validate.py --baseline-root /caminho/baseline --out /caminho/resultados/static.json
python tests/global05/browser.py --out /caminho/resultados/http
```

A última chamada usa navegação HTTP real e exige Playwright com navegador instalado; essa modalidade permanece pendente neste ambiente. Para repetir estritamente o ensaio executado aqui:

```bash
python tests/global05/browser.py --offline-fixture --out /caminho/resultados/offline
python tests/global05/pages.py --out /caminho/resultados/pages
python tests/global05/contrast.py --out /caminho/resultados/contrast.json
```

`PLAYWRIGHT_CHROMIUM_EXECUTABLE` pode indicar um executável já instalado. Não é necessário nem recomendado desativar políticas de rede do navegador.

O workflow `.github/workflows/global05-qa.yml` acompanha o patch, mas **não foi submetido ou executado no GitHub nesta sessão**. Ele exige geração determinística, testes de lógica, preservação, navegação HTTP e regressões amplas já existentes. Os testes históricos que fixam hashes de HTML anterior são provas das etapas antigas; não devem ser regravados ou tomados como evidência de aprovação desta alteração.

## Resultados do candidato local

Os relatórios entregues registram **702 verificações de interação nas seis edições**, **252 verificações auxiliares de home/hubs/alias/corpo 404**, **196 verificações estáticas**, **650 amostras de contraste**, **144 testes de lógica existentes** e **13 testes novos do finalizador** aprovados. São tipos de verificação diferentes, parcialmente sobrepostos, não uma soma de funcionalidades.

A comparação anterior reproduziu três defeitos de interação em múltiplas larguras e edições: 171 asserções falharam em 702. Isso não significa 171 defeitos diferentes. O candidato corrigido passou nas 702. A verificação da imagem Open Graph é estática e independente dessas contagens.

A geração completa do rollout, seguida da preparação do manifesto, foi repetida com **19 arquivos de saída monitorados e bytes estáveis**. Uma tentativa anterior revelou apenas reposicionamento/ordem de atributos das novas tags SP; a inserção foi ajustada à ordem do gerador e a repetição final passou. Nenhum dado político foi alterado para obter esse resultado.

Durante a construção dos ensaios, foram corrigidos o tratamento de scripts `defer`, a interpretação de foco na interface do navegador e o escape do parser de cor. Esses resultados preliminares não são apresentados como defeitos adicionais do site. O pacote conserva os relatórios finais, a reprodução da versão-base e a ocorrência de serialização do build.

## O que ainda impede o encerramento

Faltam aplicar o patch numa branch autorizada, validar o candidato por HTTP e CI, conferir o diff contra o main vigente, fazer merge e verificar os bytes e comportamentos no site publicado. Faltam também as verificações de infraestrutura descritas em `GLOBAL-INTEGRATION-PUBLICACAO.md`.

As issues #44 e #39 permanecem abertas. Q02/Q04 não são promovidas a conclusão somente pela existência deste pacote. As frentes editoriais independentes e RS/Estaduais mantêm seus próprios gates.

## Referências técnicas

- W3C, foco não obscurecido: https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html
- W3C, contraste mínimo: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- Google Search Central, canonical: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- Google Search Central, robots.txt: https://developers.google.com/search/docs/crawling-indexing/robots/intro

As referências orientam os critérios técnicos; não substituem teste da implementação nem validam as afirmações políticas presentes nas fontes do projeto.

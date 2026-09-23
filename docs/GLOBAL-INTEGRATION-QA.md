# GLOBAL-05 — QA global final

Issue #44 · epic #39.

Baseline funcional: `4a3300005fafbf85e13c4a61e763db1496924348`. Este documento registra o candidato GLOBAL-05 validado remotamente; a publicação definitiva só é considerada concluída depois do gate pós-merge descrito em `GLOBAL-INTEGRATION-PUBLICACAO.md`.

## Correções verificadas

A revisão final encontrou quatro regressões técnicas, sem nova pesquisa eleitoral:

1. **Menu mobile de SP:** o botão anunciava abertura, mas uma regra de CSS mantinha os links ocultos. A regra comum agora respeita `#siteNav.is-open` e o botão atualiza seu nome acessível.
2. **“Origem e limites” dentro de Selecionados:** o atalho abre o `details` da própria ficha original, posiciona o destino abaixo do cabeçalho do leitor e leva foco ao resumo sem apagar a consulta.
3. **Remoção de filtros:** o foco passa ao próximo filtro disponível ou retorna à busca.
4. **Metadados sociais de SP:** a edição passa a declarar imagem Open Graph/Twitter reutilizando um asset já publicado.

O finalizador `tools/global05/build.py` também mantém revisões `?v=<sha>` de CSS/JS alinhadas aos bytes atuais. Não reserializa a narrativa das fichas.

## Preservação substantiva

A suíte GLOBAL-05 compara o candidato à baseline real e exige:
- as **760 fichas** com markup original preservado;
- `cqData`, textos, IDs, destinos, fontes, associações e snapshots sem mudança editorial;
- arquivos fora do escopo byte a byte iguais;
- manifesto correspondente aos arquivos finais;
- finalização idempotente.

O verificador D4 recebeu apenas uma adaptação estreita para reconhecer esta etapa posterior, exigir a baseline GLOBAL-05 explícita e continuar protegendo o núcleo D5 e os dados políticos.

## CI candidato aprovado

Run GLOBAL-05: **35890456988**, success no merge candidate `6a0f2e6d31f1788cc5d87554121a994d184b3e85`.

Artefato **10764579302**, SHA-256 `3d94896d907d26a8d2586efcee6247b52720d6825dae50e8f47923ce08dab994`.

Resultados do mesmo candidato:
- 13 testes do finalizador GLOBAL-05;
- 144 testes JS existentes/do rollout;
- **196 checks estáticos**, **760 fichas**, **1.776 arquivos protegidos** e **3.834 referências locais**;
- **726 checks HTTP direcionados** da #44;
- **1.372 checks do rollout**;
- **392 checks de Selecionados + 25 casos adicionais**;
- **252 checks** de home/hubs/alias/404 em viewports;
- **650 amostras técnicas de contraste**, todas dentro dos limiares adotados.

Run de regressão D4 independente: **35890456936**, success no mesmo merge candidate.

Artefato **10764952087**, SHA-256 `a941c3036bde034cbf7b88f225a70bf74bf3032892bf235edd00a23ff2fc814b`.

A regressão D4 registrou **5.750 checks de preservação/rastreabilidade**, 760 fichas, 695 vínculos existentes, 1.372 checks de navegador, 23 de manutenção, 392 de Selecionados e 25 adicionais, além de segunda geração byte-estável.

## Responsividade e acessibilidade técnica

Chromium foi exercitado em 320, 360, 390, 430, 768, 1024 e 1440 px. Os testes cobrem menu, overflow, filtros, foco, Escape, dialogs, leitor original, âncoras, estados vazios e no-JS.

As capturas representativas foram inspecionadas, incluindo SP mobile, fichas longas e “Origem e limites” aberto dentro de Selecionados.

A amostragem de contraste usa 4,5:1 para texto normal e 3:1 para texto grande em componentes selecionados. **Isso não é certificação WCAG integral**, auditoria com leitor de tela ou teste em aparelho físico.

## SEO e rotas

A validação cobre 11 rotas indexáveis, alias estadual legado e 404, verificando:
- titles e descriptions;
- canonical;
- robots por página;
- Open Graph;
- sitemap;
- manifesto;
- referências ARIA;
- IDs e âncoras;
- assets locais e suas revisões.

O `robots.txt` versionado está no subdiretório do projeto GitHub Pages; não é apresentado como controle do host raiz `github.io`.

## Limites

Não houve nova coleta política, ranking, inferência de posição, mensagem real de WhatsApp, execução real de Web Share do sistema operacional, leitor de tela ou aparelho físico. Fontes políticas externas não foram refeitas para este QA.

A evidência de publicação definitiva é registrada na issue #44 e no PR correspondente depois do merge. O epic #39 somente pode fechar após esse gate público. A #50 permanece posterior.

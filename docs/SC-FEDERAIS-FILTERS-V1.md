# SC/Federais — filtros por pautas, Round 2

Continuidade da issue #20. Implementação isolada em `feat/sc-federais-filtros-v1`, originada de `89092b6192f5b06acba3fcb1ac7adef1af99b266`.

## Comportamento público

No desktop, a seção **Filtrar por pautas** fica abaixo dos partidos. A sidebar possui rolagem vertical própria, limitada pelo espaço entre navbar e rodapé. No mobile e tablet até 980 px, **Pautas · Filtrar** abre um diálogo nativo, com fechamento, foco e resultado. Há um único painel no DOM: ele muda de contêiner no breakpoint, sem copiar IDs nem manter seleções divergentes.

**Pelo menos uma** é o padrão OR. **Todas** usa AND. A busca textual é aplicada junto com o filtro. **Limpar pautas** conserva a busca; **Limpar tudo**, no estado vazio, remove ambos. As categorias ficam em ordem alfabética, com apresentação uniforme. Seus números são totais de candidaturas da edição, não quantidades de fontes, e não são condicionados às seleções ou à busca. Categorias sem apoio elegível ficam fora dos botões, mas continuam no catálogo documental.

A seleção não reordena elementos. A ordem diária existente continua sendo calculada pelo código original. O índice dos partidos acompanha apenas os grupos com resultados; ao limpar, sua ordem e seus totais originais reaparecem.

Cada resultado filtrado mostra **Neste filtro**, com a prioridade ou apoio específico e as fontes correspondentes. Não se exibe a fórmula enganosa “apoia + nome da família”. Links para fichas ocultadas removem os critérios que impediam a exibição, apresentam uma mensagem e revelam/focam o destino. Links para **Fontes e contexto** abrem o bloco correspondente.

## Limites editoriais

O filtro consome exclusivamente `eligible_current_support` de `data/sc-federais-topics-v1/matrix.json`, com `direction`, `position_target`, `period` e `source_ids` intactos. Não pesquisa palavras para criar associações. Não usa `data-has-pauta` como prova de elegibilidade. Não atribui pautas por partido, identidade, nome, profissão ou biografia.

Oposição isolada, debate, atuação sem declaração de apoio, documentos históricos, período indeterminado e atribuição conjunta pendente não são promovidos a apoio. Permanecem nos textos e evidências originais. Ausência de tag significa associação não documentada neste recorte, não oposição nem ausência de propostas. Nenhuma contagem é ranking, nota ou recomendação.

A revisão documental é datada de 21/09/2026. A rotação diária não atualiza fatos eleitorais ou posições. Não foram feitas novas atribuições políticas nesta implementação.

## Arquitetura e reprodução

- `assets/pauta-filter-core.js`: funções puras de normalização, interseção da busca e união/interseção de temas. Aceita a ordem atual sem modificá-la.
- `assets/pauta-filters.js`: interação, foco, painel único, resultados e fontes.
- `assets/pauta-filters.css`: estilos isolados.
- `tools/sc_federal_filters/build.py`: gera controles e dados somente a partir do catálogo e da matriz aprovados; reaplicação idempotente.
- `assets/sc-federais-filters-data.js`: payload gerado para consumo sem requisição adicional de JSON.
- `data/sc-federais-filters-v1/payload.json` e `manifest.json`: dados públicos consumidos e hashes das fontes documentais.
- `tests/sc_federais_filters.test.cjs`: comparação independente com a matriz, incluindo combinações de dois e três temas, busca e rotação.
- `tools/sc_federal_filters/qa.py`: preservação da base efetiva, integridade de associações e testes Chromium em sete larguras.
- `tools/sc_federal_filters/verify_live.py`: HTTP/SHA-256 e interação no Pages real.

Na raiz, com Python 3.12, Node e dependências de teste:

```sh
pip install beautifulsoup4==4.15.0 playwright==1.63.0
python -m playwright install --with-deps chromium
python tools/sc_federal_filters/build.py
node --test tests/sc_federais_filters.test.cjs
PRESERVATION_BASE=<commit-base-efetivo> python tools/sc_federal_filters/qa.py
```

Após atualizar a pesquisa, a ordem de compilação é: revisão editorial, matriz temática e, por último, `tools/sc_federal_filters/build.py`. O último passo restaura a explicação atual dos filtros no HTML sem reescrever os snapshots históricos. Os campos `filters_active:false` do Round 1 documentam aquela entrega; `data/sc-federais-filters-v1/manifest.json` registra a ativação somente em SC/Federais.

O HTML é alterado por blocos marcados `eef-filters:*` e por um adaptador mínimo na busca original. O QA retira esses blocos e compara o restante com a base do PR. Cards, dados eleitorais, imagens, navbar, hero, rodapé, fonte da matriz e demais frentes devem permanecer intactos. Não se deve substituir o index atual por uma cópia antiga.

## Acessibilidade e falhas

Botões têm `aria-pressed`; modos são radios nativos; o diálogo usa `aria-labelledby`, foco inicial, retenção de Tab, Escape, botão fechar e devolução de foco. O botão de resultados leva ao conteúdo. A passagem de mobile para desktop fecha o diálogo e move o mesmo painel. Há limite de altura e rolagem interna para telas baixas.

Os controles permanecem ocultos até o carregamento e validação dos dados. Sem JavaScript ou na falha de um asset, as fichas permanecem legíveis; a busca original continua disponível quando seu próprio script está funcional. Fontes entram como texto e URLs validadas, não como HTML arbitrário.

As escolhas ficam exclusivamente em memória. Não são gravadas em localStorage/sessionStorage/cookies, não entram na URL e não são transmitidas à API de métricas. A configuração de métricas existente não é ativada por este trabalho.

Referências técnicas: padrão de diálogo WAI-ARIA APG (`https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/`) e documentação do diálogo nativo (`https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog`).

Os testes automatizados não equivalem a uso com leitor de tela real nem a ensaio em aparelhos físicos. Imagens externas são bloqueadas no QA para não depender de servidores de campanha.

## Replicação posterior

Esta entrega **não ativa filtros em outras páginas**. Para replicar, cada frente deve fornecer sua própria matriz aprovada e uma configuração de edição, preservar seus IDs/âncoras e adotar o mesmo contrato de elegibilidade. Reutilizar o motor e o painel, nunca as associações entre candidaturas. Recalcular contagens e cobertura, adaptar os pontos de montagem e executar os testes de preservação e publicação sobre a nova base.

Mudança de tema ou de sentido exige o versionamento previsto em `docs/TOPICS-V1-CONTRACT.md`. Não usar aliases como classificação automática. A verificação de publicação e o fechamento da issue serão registrados somente depois de seus resultados reais.

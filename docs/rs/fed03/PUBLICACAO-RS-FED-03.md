# Publicação RS-FED-03 — 21/09/2026

## Entrega e cobertura

A rodada de pesquisa dos 63 alvos originais foi executada, integrada pelo PR #17 e publicada na rota existente. O projeto continua com lacunas editoriais; a issue #1 permanece aberta.

URL: https://selvalabs.github.io/esquerda-em-foco/rs/deputados-federais/

PR: https://github.com/selvalabs/esquerda-em-foco/pull/17

Commit de integração: `4d6ee6952ba4b85cee189d297c886f5e13003872`.

Foram registradas 120 consultas individuais para os 63 alvos. Vinte fichas ganharam síntese de pautas/atuação; a cobertura desse campo passou de 44 para 64. O total de sínteses passou de 46 para 65, porque uma das vinte substituiu conteúdo antes classificado apenas como trajetória.

Durante o trabalho, uma correção de recorte no main acrescentou dois registros do PSTU e dois da REDE. A integração preservou essa ampliação: a base atual contém 111 registros e 111 fotografias oficiais, com 110 deferidos e uma renúncia no snapshot consultado. O manifesto original de 63 alvos foi mantido e os quatro registros novos receberam triagem separada.

Estado final: 64 fichas com pautas/atuação, uma apenas com trajetória e 46 sem síntese suficiente. Há 47 pendências de pautas/atuação: 43 do lote original e quatro recém-incorporadas. Uma síntese não certifica completude dos demais campos de uma ficha.

Biografias: 24. Cargos eletivos confirmados: 17. Histórico anterior: 84 fichas; alguma votação nominal conferida: 81 fichas. A auditoria de cargos não é exaustiva.

## Históricos nominais

Dos oito registros originais pendentes, um valor nominal foi recuperado, cinco ausências foram qualificadas por cadastro histórico inapto e dois conflitos de nome civil continuam sem resolução. Nenhuma ausência foi convertida em zero e as situações históricas não foram apresentadas como situações de 2026.

A ampliação do recorte trouxe três lacunas adicionais. O conjunto atual contém 277 valores nominais conferidos, 21 casos sem votação nominal individual aplicável, cinco ausências históricas qualificadas e cinco registros ainda não reconciliados.

## Limitação da reconsulta eleitoral

Os 111 cadastros foram reconciliados nos arquivos CSV oficiais. As 111 novas tentativas de acesso aos perfis individuais retornaram bloqueio HTTP 403. Foram preservados os snapshots anteriores, sem declarar essas tentativas como reconferências bem-sucedidas.

## Validação técnica

Validação pré-integração: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35646396083

Validação adicional no main integrado: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35647359326

Ambas concluídas com sucesso: 51 testes RS e três testes do recorte canônico; 173 verificações gerais Chromium e 27 verificações adicionais nos cards alterados, totalizando 200 verificações de navegador. A reconstrução dos quatro arquivos públicos principais foi determinística. A validação adicional confirmou que seus bytes permaneceram idênticos aos já publicados.

Os testes de preservação de SC consultam os bytes do commit Git em uso, não uma versão histórica obsoleta nem os bytes da cópia de trabalho. Isso preserva atualizações independentes legítimas de SC, sem enfraquecer a detecção de modificações locais.

## Publicação e preservação

Deploy Pages concluído: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35646917545

Verificação pública concluída: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35646918283

Em `2026-09-21T19:46:35.785183+00:00`, foram conferidos 124 arquivos com HTTP 200 e SHA-256 coincidente: os 120 arquivos da rota RS, as páginas federal/estadual de SC, sitemap e robots. O relatório integral está no artefato `rs-fed03-live-verification` desse run e no pacote de entrega.

O pai real da integração foi `a763b6ee0bcdc8fb635310fc40560b5296e7d4bf`. A comparação confirmou zero alterações inesperadas fora dos caminhos do RS e workflows próprios. Os filtros de SC publicados paralelamente foram preservados. O sitemap e a configuração compartilhada do recorte não foram alterados pelo RS-FED-03.

## Hashes da publicação verificada

- HTML RS: `60dcf1b1f21fc830af7fad4fdc92a0a3f06cb581c7fbdb574473ca3d750e4a43`
- `dados.json`: `35474cd2af5d80952434a3c5b75d16654c206bb8b55672b179adebc0a81c800f`
- `fontes.json`: `ead7c12f9239dc2afb1db6bf98ef1cfa2733a8a4580fe84ccfed512cd20fa00a`
- `revisao.json`: `810d2eb80d39762ade4dcf0d1ae45b02441074ea23aaad1e560af2ecb2b1517e`
- Relatório integral de verificação pública: `8a2f0b15896b97dd8d67ddfc367991f24287aebedbfb85cefd9fff29777f11ad`

## Continuidade e entrega

A issue #1 foi atualizada com os números correntes. Não há novos filtros visuais nem atualização recorrente instalada. A base é datada de 21/09/2026.

Dados e controles: `data/rs/fed03/`; matrizes, decisões, logs e testes: `docs/rs/fed03/`. Procedimento de manutenção: `ATUALIZACAO-MANUAL.md`.

O pacote final inclui a página publicada, imagens, dados, scripts e auditorias, mas não o HTML raiz de SC, arquivos de outras frentes, fontes tipográficas, caches Python ou textos integrais dos artigos coletados. A página já está pronta para ser servida. Para reconstrução, usar o checkout completo do repositório conforme o procedimento documentado.

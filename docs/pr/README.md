# Paraná — base cadastral 2026

## Estado da entrega

Cadastro reconciliado em 21/09/2026: 218 registros (109 federais e 109 estaduais), 218 consultas individuais TSE lidas e 218 fotos oficiais. O recorte contém PCdoB, PCO, PDT, PSB, PSOL, PT, PV e UP; não representa todas as candidaturas do Paraná.

A camada editorial é parcial: 17 sínteses individuais (11 federais e 6 estaduais), com 48 associações de pautas apoiadas em fontes. Restam 201 fichas sem síntese individual de pautas. Não se preenchem essas lacunas por filiação, profissão ou suposição. Algumas fontes municipais foram lidas apenas pela indexação institucional, devido a bloqueio da página integral; essa limitação acompanha as respectivas fichas.

## Totais do recorte

| Campo | Federais | Estaduais |
|---|---:|---:|
| Registros | 109 | 109 |
| Aptas na consulta individual | 105 | 104 |
| Inaptas na consulta individual | 4 | 5 |
| Fotos oficiais | 109 | 109 |
| Com candidaturas anteriores vinculadas | 78 | 89 |
| Registros históricos com votos consolidados | 177 | 214 |
| Pautas individuais documentadas | 11 | 6 |
| Mandato atual confirmado nesta coleta | 10 | 3 |

A situação processual e a aptidão são campos separados. Há nove registros com indeferimento em recurso classificados pelo próprio TSE como aptos na consulta. Oito renúncias e um indeferimento inapto permanecem no cadastro. Cinco vínculos de substituição são exibidos reciprocamente. Pessoas com registros para cargos diferentes não são deduplicadas pelo nome.

## Arquivos e fontes

- `data/pr/candidates-official.json`: subconjunto público do cadastro; `manifest.json`: URL, horário, hash do ZIP e hash do CSV interno.
- `profiles-official.json`: campos públicos permitidos da consulta individual; `status-extended.json`: vínculos e situações complementares.
- `history-official.json` e `votes-official.json`: histórico vinculado por identificador TSE e votos agregados para 2012, 2014, 2016, 2018, 2020, 2022 e 2024. Os ZIPs de votação foram lidos por intervalos HTTP com CRC e SHA-256 do membro PR completo; não há alegação de hash do ZIP inteiro.
- `editorial.json`: sínteses manuais e suas evidências. Cada tag tem fonte individual; declarações próprias são identificadas como tais. Proposta não equivale a lei, execução ou resultado.
- `offices-verified.json`: confirmação institucional de 13 mandatos parlamentares. Ausência não significa ausência de mandato, especialmente municipal.
- `docs/pr/*-audit.json`: pendências identificadas por registro, inclusive pautas, votos históricos parciais, mandato e atuação territorial.
- `docs/pr/qa/report.json`: resultado real dos testes de navegador. A mera existência de um workflow não comprova aprovação.

Fonte cadastral: https://dadosabertos.tse.jus.br/dataset/candidatos-2026 . Arquivo gerado em 21/09/2026 às 12:31:37; consultas complementares têm datas próprias no manifesto. A situação pode mudar após essa extração.

## Páginas

`/pr/`, `/pr/deputados-federais/` e `/pr/deputados-estaduais/`. Cada edição oferece JSON, CSV, fontes e auditoria. Busca, partido, aptidão, mandato confirmado, histórico e pautas combinam-se com lógica AND. A região refere-se apenas à atuação municipal documentada em quatro fichas, não a uma base eleitoral inferida. URLs preservam os filtros.

O código reutiliza a apresentação e o componente de ficha do RS em modo somente leitura. Os arquivos de SC e RS são protegidos por comparação de hashes. Não se altera a navegação das edições anteriores; os endereços PR são independentes. A reconciliação com uma futura taxonomia compartilhada permanece explicitada em `taxonomy.json`.

## Reprodução a partir da raiz do repositório

```sh
python -m pip install beautifulsoup4==4.13.4 lxml==6.1.3 pillow==12.3.0 playwright==1.63.0
python tools/pr/build.py
python -m unittest discover -s tests/pr -p 'test_*.py' -v
python -m playwright install --with-deps chromium
python tools/pr/qa.py
```

Os coletores preservam os snapshots existentes. Para uma atualização eleitoral, criar um novo snapshot versionado e revisar os totais esperados antes de substituir a base; não apagar silenciosamente os arquivos antigos. O identificador REST da eleição é descoberto em `/eleicao/ordinarias` e não é confundido com `CD_ELEICAO` do CSV.

Para servir, publicar a pasta `pr/` junto ao site existente. O HTML não depende de React, API de produção ou reescrita de SPA. Na migração de domínio, reconstruir com `EEFOCO_SITE_URL` apontando à raiz pública correta para atualizar canonical e sitemap.

## Fora da conclusão cadastral

A pesquisa editorial não está concluída para todos os registros. Falta ampliar as 201 sínteses restantes, conferir outros mandatos atuais e regiões com evidência, completar votos históricos onde possível e produzir análise individual de votações parlamentares. Os votos eleitorais históricos presentes na base não são votos em projetos de lei. Essas pendências não impedem a consulta do cadastro, mas impedem declarar encerrado o escopo editorial integral da issue #7.

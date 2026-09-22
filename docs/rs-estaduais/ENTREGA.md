# RS / Deputados estaduais 2026 — entrega técnica e cobertura

**Data da pesquisa:** 2026-09-21. **Snapshot TSE:** 21/09/2026 12:31:37.

**Situação:** interface e cadastro aprovados nos testes; pesquisa editorial aprofundada parcial, com lacunas identificadas por candidatura. Não se declara encerrado o escopo editorial completo.

## O que foi entregue

A edição reúne 149 candidaturas do recorte, de um universo oficial de 542 registros de deputado estadual no RS. Todos os registros foram conciliados com fichas individuais do DivulgaCand e receberam retrato oficial. A extração não remove silenciosamente situações eleitorais diferentes de deferimento.

A pesquisa oferece 61 sínteses individuais de pautas ou temas documentados, atos institucionais em 31 fichas e 16 mandatos atuais confirmados institucionalmente. Existem 124 candidaturas com histórico eleitoral anterior vinculado e votos nominais conferidos para 122 candidaturas, em 395 registros históricos.

A página possui busca sem distinção de acentos, filtros por partido, situação e histórico anterior, ordem diária determinística no fuso de São Paulo, links diretos para fichas, histórico expansível, fontes, retratos locais e downloads JSON/CSV. Não há pontuação, preferência editorial, previsão de eleição, rastreamento ou dados privados de cadastro nos exports.

## Cobertura por partido

| Partido | Registros | Sínteses de pautas | Atos documentados | Mandatos atuais confirmados |
|---|---:|---:|---:|---:|
| PCdoB | 6 | 6 | 3 | 2 |
| PDT | 47 | 14 | 6 | 3 |
| PSB | 24 | 6 | 2 | 1 |
| PSOL | 21 | 8 | 4 | 2 |
| PSTU | 2 | 0 | 0 | 0 |
| PT | 40 | 24 | 16 | 8 |
| PV | 5 | 1 | 0 | 0 |
| REDE | 2 | 1 | 0 | 0 |
| UP | 2 | 1 | 0 | 0 |

O PCO está no recorte herdado de RS/federais, mas não tem registro selecionado neste snapshot. A tabela descreve a cobertura da pesquisa, não avalia candidaturas ou partidos.

## Validações

- Cadastro: identificadores, cargo, UF, número, partido, situação e conciliação individual. Testes unitários: PASS.
- Navegador Chromium: 63 verificações; resultado PASS. Larguras 320, 360, 390, 768, 1024 e 1440, sem overflow horizontal nas verificações.
- Retratos: correspondência ao identificador TSE, integridade SHA-256 e carregamento de todas as imagens.
- Isolamento: o workflow bloqueia mudanças em SC/federais, SC/estaduais, RS/federais, navegação global, assets compartilhados, servidor e sitemap principal.
- SEO: canonical e metadados próprios, Open Graph, coleção estruturada sem posições classificatórias, manifesto e sitemap locais.

## Pendências concretas

Faltam sínteses de pautas verificadas para **88 candidaturas**. Os nomes e próximos passos estão em `candidate-coverage.csv` e `candidate-coverage.json`. Cadastros e biografias eleitorais disponíveis não são apresentados como substitutos de um programa individual.

A confirmação de mandatos atuais não foi concluída para todo o recorte. Perfis de campanha, resultados antigos e votações históricas não foram usados para inferir automaticamente exercício de cargo na data da pesquisa. A indisponibilidade de algumas páginas institucionais está registrada nos arquivos de consulta.

Também restam votos de parte das disputas históricas, pesquisa mais ampla de projetos/comissões e verificação detalhada de fontes externas além dos endereços declarados. Nenhuma ausência de dado significa ausência de atuação.

## Organização e reprodução

- `data/rs-estaduais/`: projeções oficiais, metadados de origem, fotos, histórias, votos e revisão editorial.
- `rs/deputados-estaduais/`: página e recursos públicos da edição.
- `tools/rs-estaduais/`: coleta, conciliação, pesquisa, renderização, QA e relatório.
- `tests/rs-estaduais/`: invariantes de dados, fontes, privacidade e isolamento.
- `docs/rs-estaduais/`: baseline, testes, capturas, cobertura e pendências.

```bash
python tools/rs-estaduais/collect.py
python tools/rs-estaduais/research.py
python tools/rs-estaduais/votes.py
python tools/rs-estaduais/finalize_sources.py
python tools/rs-estaduais/build.py
python -m unittest discover -s tests/rs-estaduais -p 'test_*.py' -v
python tools/rs-estaduais/qa.py
```

A coleta reaproveita o snapshot congelado. Atualizações eleitorais devem gerar uma nova edição auditada, com comparação das situações; não basta alterar a data de publicação. Os dados na pasta `raw` são projeções de colunas necessárias, e não uma cópia integral de cadastros pessoais. Hashes distinguem ZIP completo recebido de membro extraído por acesso parcial.

## Publicação

A rota preparada é `/rs/deputados-estaduais/`. Esta entrega não altera a homepage, a navegação global nem o sitemap principal. Um arquivo de página gerado e um workflow verde, isoladamente, não comprovam que o endereço já foi publicado. O merge e o deploy devem ser verificados separadamente.

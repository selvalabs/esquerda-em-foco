# Deputados estaduais de Santa Catarina — Revisão 2

Frente independente do Esquerda em Foco, publicada em `/esquerda-em-foco/deputados-estaduais/`. A revisão não integra a navegação das frentes e não altera os arquivos federais de SC ou do RS.

## Retrato desta revisão

A reconciliação de 21/09/2026 mantém 97 candidaturas no recorte, entre 414 registros para deputado estadual em SC: 94 deferidos e três em situação recursal. A inclusão se dá pelas siglas consideradas no projeto — PT, PCdoB, PV, PSOL, REDE, PDT, PSB, PSTU, UP e PCO — e não por uma classificação individual de ideologia. O relatório `audit/review2/tse-diff.json` registra inclusões, ausências e alterações, sem retirar nomes silenciosamente.

A cobertura efetiva é calculada em `audit/review2/report.json`, incluindo cadastros, registros de consulta individual, leituras com evidência, sínteses de pautas, biografias adicionais e limites de confirmação de mandatos. A quantidade de fichas não é usada como sinônimo de pesquisa editorial completa. Todas apresentam a trajetória eleitoral disponível no histórico vinculado pelo TSE; uma biografia adicional exige outra fonte individual.

Mandatos distinguem composição institucional atual, licença documentada, exercício por suplência, atividade institucional datada, referência localizada apenas no índice de busca e relato da própria candidatura. Redução no total de confirmações institucionais não significa perda de mandato. As situações não confirmadas permanecem explícitas.

## Correções importantes

A votação histórica não é mais somada apenas por ano e identificador. Identificadores curtos dos arquivos antigos podem se repetir em municípios diferentes. O cruzamento agora considera ano/ciclo do arquivo, UF, unidade eleitoral, cargo, número, turno, data real e tipo de eleição, além do identificador da pessoa. Para vice-candidaturas, a votação é explicitamente a da chapa. Quatorze totais de 2004 foram corrigidos; o antes/depois está em `audit/review2/votes-audit.json`.

Eleições suplementares aparecem no ano de sua realização, mantendo separadamente o ciclo do arquivo de origem. A disputa suplementar de Brusque em setembro de 2023, armazenada pelo TSE no conjunto do ciclo 2020, não é confundida nem somada com a disputa regular de 2020.

Dos 231 registros históricos, 229 totais foram conciliados. Ângelo Chocolate/2012 e Meirinho/2022 continuam com valor ausente (`null`), nunca convertido em zero. Um zero publicado exige a existência de linhas efetivamente encontradas no arquivo oficial.

A referência genérica anteriormente usada para atribuir uma pauta a Gui Pereira foi substituída pela página individual do PL 19.784/2025, com autoria e data. O projeto não é apresentado como lei aprovada. Endereços de redes sociais preservam a caixa do caminho e dos parâmetros; caminhos de publicações não são convertidos indiscriminadamente para minúsculas.

## Estrutura e reprodução

Python 3.12+, BeautifulSoup, Pillow e Playwright. A partir da raiz do repositório:

```sh
pip install beautifulsoup4 pillow playwright
python deputados-estaduais/tools/build.py
python -m playwright install chromium
python deputados-estaduais/tools/qa.py
python deputados-estaduais/tools/review2_qa.py
```

O build é determinístico a partir do snapshot revisado: não faz uma coleta implícita nem modifica outras frentes. Ele verifica os hashes dos arquivos protegidos antes e depois. `--preview` em `review2_build.py` permite uma prévia local de um pacote incompleto, mas registra a verificação de isolamento como incompleta; essa opção não é aceita pelo fluxo de publicação.

Uma nova atualização começa em branch própria. Execute explicitamente `review2_collect.py`, `review2_votes.py`, `review2_portraits.py`, `review2_sources.py` e, quando necessário, `review2_browser_sources.py`. Reveja o diff e as fontes antes de reconstruir. Mudanças no conjunto de candidatos exigem revisão individual dos novos registros; mudanças legítimas em outras frentes exigem renovar a referência de isolamento de forma documentada, sem sobrescrever os arquivos.

`editorial/review2.json` é a entrada editorial por ID TSE. Inclui fontes, datas, tipos de material, consultas efetuadas e limites de confirmação. `editorial/perfis.json` é apenas uma projeção de compatibilidade gerada para o layout. `data/candidaturas.json` tem schema 2, com dados cadastrais, histórico, trajetória, pauta, proveniência e situação. `data/candidaturas.csv` oferece uma exportação resumida.

A rota e os links diretos `#candidato-<ID_TSE>` permanecem. A interface adiciona filtro de situação cadastral, explicações expansíveis, canais declarados e cobertura da revisão. Não há notas, rankings, previsões eleitorais, formulário de campanha, login ou rastreamento nesta frente.

## Auditoria e limites

`audit/review2/collection.json` identifica os arquivos oficiais e suas gerações; `votes-audit.json`, `portraits-audit.json`, `link-checks.json`, `browser-sources.json`, `report.json` e `qa.json` registram evidências, correções e testes. O relatório de QA distingue validação estrutural da cobertura editorial.

HTTP 200, título de página e presença de um link não confirmam o conteúdo de uma afirmação. CAPTCHA, bloqueio automatizado, erro e ausência de material suficiente são estados diferentes. Fontes próprias, partidárias, institucionais, entrevistas e materiais históricos recebem atribuição; não se infere pauta pelo partido, nome, profissão ou identidade.

Textos integrais de terceiros e capturas de revisão não integram o site: `audit/source-extracts.json` e `audit/screenshots/` permanecem ignorados pelo Git. CPF, título eleitoral, data de nascimento e e-mail pessoal não são exportados pelo coletor desta revisão. Novas coletas dependem de execução e revisão explícitas; o site não promete atualização em tempo real.

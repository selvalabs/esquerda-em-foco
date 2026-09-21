# Deputados federais do Rio Grande do Sul — 2026

Edição independente do Esquerda em foco. Rota: `/rs/deputados-federais/`, sob o prefixo do projeto no GitHub Pages. Desenvolvimento autorizado na issue #1.

## O que esta edição contém

O cadastro consultado em 21/09/2026 tem 107 registros para as mesmas oito siglas da edição federal de SC. Sete têm registros: PCdoB 2, PDT 32, PSB 23, PSOL 23, PT 21, PV 3 e UP 3. O PCO faz parte do recorte, mas não tem registro para esse estado/cargo na extração. O universo completo de candidaturas federais do RS contém outras siglas; a página não se apresenta como um catálogo de todos os partidos.

São 106 registros deferidos e um com renúncia, identificado na própria ficha. A contagem de 107 não equivale ao número de candidaturas ativas. Cadastro, situação, fotografia e perfil individual do TSE foram conferidos para os 107 registros, usando o identificador eleitoral e não apenas semelhança de nomes.

Há histórico anterior vinculado para 82 candidaturas, confirmação institucional de nove mandatos federais atuais e 24 sínteses individuais de pautas com referências. As outras 83 fichas declaram a ausência de síntese documental nesta edição. Isso não significa que essas candidaturas não tenham propostas. Um mandato não confirmado também não é tratado como mandato inexistente. A presença de todas as fichas não significa pesquisa biográfica exaustiva sobre todas as pessoas.

A cobertura atual e os resultados efetivos dos testes estão em `build-report.json`, `candidate-audit.json`, `unit-tests.txt` e `browser-qa.json`. O último arquivo só marca `passed: true` se todos os testes executados tiverem passado.

## Fontes e limites

Os arquivos oficiais, datas e hashes ficam em `data/rs/manifest.json`. Situação eleitoral, redes, fotos, históricos e perfis individuais são guardados separadamente. Os sites e redes exibidos foram declarados ao TSE; a declaração não garante disponibilidade do endereço nem comprova todo o conteúdo publicado. Endereços inválidos não são substituídos por perfis adivinhados.

`data/rs/editorial.json` contém apenas resumos individuais com fontes. Publicações de campanha são atribuídas como tais; não se presume implementação das propostas. Não há notas, avaliação de candidaturas, recomendação de voto, previsão de resultado ou classificação de competitividade.

Os históricos são vinculados pelo TSE e discriminados por ano, cargo, local e resultado. A cidade de uma disputa anterior não é tratada como domicílio atual. A contagem de disputas inclui 2026, reúne turnos do mesmo registro e não representa quantidade de mandatos. Votos anteriores, quando conferidos, são nominais e identificados por ano e turno; um campo não apurado não significa zero. Votos de vice não são convertidos em votação nominal individual.

A tentativa inicial de baixar os arquivos de votação de 2022 e 2024 recebeu HTTP 403. `tools/rs/votes_ranges.py` faz uma segunda leitura pelos intervalos HTTP públicos do próprio arquivo oficial, validando status 206, posição, tamanho, CRC do ZIP e SHA-256 do membro RS integralmente lido. Essa leitura não afirma ter calculado o hash do ZIP inteiro quando somente partes foram transferidas. O resultado, inclusive eventual falha, fica em `votes-ranges.json`; totais só entram nas fichas depois de uma reconciliação válida.

CPF, título eleitoral, e-mail pessoal, data de nascimento e endereço residencial não são publicados pelo coletor. As fotografias são oficiais, não sintéticas. Não há rastreador, captura de contatos, cookies de segmentação ou consulta de API eleitoral no navegador.

## Isolamento

O design de referência foi congelado no commit `71d123b909cdbf3d84bd1cdca89511890759d395`. O gerador lê esse HTML, mas não modifica o HTML federal de SC. Toda saída pública própria fica em `rs/deputados-federais/`; os dados de trabalho, ferramentas e auditorias ficam em `data/rs/`, `tools/rs/`, `tests/rs/` e `docs/rs/`.

A única edição compartilhada planejada é acrescentar a URL do RS ao sitemap, preservando as entradas existentes. A integração deve preservar as alterações posteriores de `main`, inclusive a frente de deputados estaduais. O hash da referência antiga não deve ser usado para sobrescrever a versão mais recente de SC.

## Construção e validação

A partir da raiz de um clone completo do repositório:

```sh
python -m pip install beautifulsoup4==4.13.4 lxml==6.1.3 pillow==12.3.0 playwright==1.63.0
python tools/rs/votes_ranges.py
python tools/rs/build.py
python tools/rs/finalize.py
python -m unittest discover -s tests/rs -p 'test_*.py' -v
python -m playwright install --with-deps chromium
python tools/rs/qa.py
```

Os testes de preservação da branch comparam seu HTML de referência com o hash congelado. Depois da integração, a preservação da versão atual de SC é verificada comparando os blobs antes e depois do merge; não se deve restaurar a referência antiga para satisfazer um teste. Os workflows de pesquisa e geração são restritos à branch RS, não executam na publicação de outras frentes.

O teste de navegador usa HTTP real com o prefixo do GitHub Pages e também sem ele, simulando a raiz de uma VPS. Verifica sete larguras, fotos locais, busca, menu, âncoras, histórico expansível, ausência de excesso de largura, rotação diária e recursos de SEO. As capturas de revisão acompanham a auditoria.

## Ordem e navegação

A lista parte da ordem alfabética e avança uma posição por dia, usando a data de Brasília e 21/09/2026 como referência. A ordem fica estável no mesmo dia, independente do fuso do visitante. O número eleitoral permanece; não há numeração de posição editorial. A regra é explicada na própria página.

A busca por uma sigla exata usa a filiação de 2026, não partidos de eleições passadas. Outros termos pesquisam nome, número, ocupação e texto documental da ficha. Os links individuais usam o identificador TSE, não a posição visual.

## Publicação e atualização

O servidor entrega apenas arquivos estáticos. Não é necessário instalar Python ou Playwright na VPS. O pacote público é a pasta `rs/deputados-federais/`. Para um domínio futuro, `EEFOCO_SITE_URL` ajusta canonical, sitemap e metadados durante a geração. Não é preciso alterar o HTML de SC.

Esta entrega não instala atualização automática dos dados eleitorais. A rotação da apresentação é automática; a coleta e a revisão de fontes não são. Novas decisões, substituições e fontes exigem nova coleta, validação e publicação. Não confundir as duas coisas.

# Deputados estaduais de Santa Catarina — 2026

Frente independente do Esquerda em foco. Endereço de publicação:

https://selvalabs.github.io/esquerda-em-foco/deputados-estaduais/

## Limite de alteração

Esta entrega acrescenta somente a pasta `deputados-estaduais/` e workflows novos de preparação na branch de trabalho. Não modifica o HTML federal, seus dados, a navbar federal, o sitemap da raiz ou a configuração de hospedagem já existente. A integração entre as duas frentes é uma etapa posterior.

O HTML gerado é estático, inclui todas as fichas no documento e usa apenas seus próprios arquivos CSS, JavaScript, imagens e dados. Não há serviço de autenticação, rastreadores, formulário de campanha, avaliação de candidaturas ou chamada de API no navegador.

## Dados e critérios

O universo é o cadastro oficial de candidaturas estaduais de SC de 2026. O recorte editorial considera PT, PCdoB, PV, PSOL, REDE, PDT, PSB, PSTU, UP e PCO. A inclusão é feita pela filiação registrada, não por classificação pessoal de ideologia. Siglas sem registros no arquivo consultado não geram seções vazias. Partidos e nomes são exibidos em ordem alfabética.

`data/candidaturas.json` contém o resultado consolidado, os históricos e suas fontes. `data/candidaturas.csv` oferece um resumo. Os arquivos oficiais de referência e seus hashes constam em `audit/collection.json` e `audit/official.json`, quando disponíveis. `audit/summary.json` informa a cobertura efetiva; não confundir presença de uma ficha com pesquisa completa de todas as suas pautas.

Resultados de eleições anteriores não comprovam exercício atual. A titularidade documentada, uma licença conhecida e o exercício por suplência são apresentados separadamente. Fontes institucionais e informações dos próprios mandatos recebem identificação. Datas históricas não são apresentadas como fatos novos.

A contagem de pleitos inclui 2026 e reúne os turnos da mesma disputa. É restrita ao histórico individual vinculado pelo TSE. A cidade de uma disputa antiga não é tratada como endereço ou domicílio atual. Votos de vice-prefeito e vice-governador são votos da chapa, não votação nominal individual.

As pautas são sínteses de publicações identificadas, não promessa de resultados nem avaliação editorial. Informações não consolidadas permanecem explícitas. CPF, título eleitoral, e-mail pessoal e data de nascimento não são exportados pelo coletor.

## Atualização e reprodução

Python 3.12 ou superior, BeautifulSoup, Pillow e Playwright:

```sh
pip install beautifulsoup4 pillow playwright
python deputados-estaduais/tools/collect.py
python deputados-estaduais/tools/build.py
python -m playwright install chromium
python deputados-estaduais/tools/qa.py
```

Executar a partir da raiz do repositório. O coletor lê o HTML federal apenas para preservar uma referência visual e registrar seu hash. A compilação escreve exclusivamente na pasta estadual. `review_patch.py` registra correções idempotentes de semântica e texto nos geradores estaduais; não opera fora dessa pasta. O adaptador `http_archive.py` valida posição, tamanho e integridade estrutural dos fragmentos recebidos antes de abrir os ZIPs públicos do TSE.

Os scripts antigos `enrich.py` e `votes_light.py` são auxiliares de diagnóstico e não integram o caminho normal da compilação. A entrada oficial é `build.py`.

A pesquisa de sites públicos guarda os textos completos somente no artefato privado de revisão do workflow. `audit/source-extracts.json` e as capturas de tela estão no `.gitignore`; não são conteúdo publicado no site.

## Testes e publicação

`audit/qa.json` registra verificações de largura em 360, 390, 768 e 1440 pixels, navegação fixa, menu móvel, busca, filtros, histórico expansível, links diretos e preservação do hash federal. As imagens de revisão ficam no artefato do workflow. O teste de navegador não substitui a conferência editorial dos dados.

Após revisão, a publicação ocorre pela inclusão da pasta na branch servida pelo GitHub Pages. Não são necessárias dependências de execução no servidor, alterações no arquivo federal ou mudanças no serviço de hospedagem.

O retrato tem data explícita. Esta entrega não instala atualização recorrente: novas situações cadastrais, substituições e fontes precisam de nova coleta e revisão antes de outra publicação.

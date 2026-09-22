# SP — Round C: interface de deputados federais

## Abrir a edição

Na raiz de um checkout desta branch, iniciar um servidor estático:

```powershell
py -m http.server 8000
```

Abrir `http://localhost:8000/sp/deputados-federais/`. A entrada de São Paulo está em `/sp/`. Não é necessário backend, banco ou chave de API para consultar e filtrar a página. A reconstrução usa fontes congeladas no repositório; não recolhe implicitamente dados eleitorais.

O servidor acima serve a pasta local, não publica o site. Para encerrar, usar Ctrl+C. O HTML funciona sem JavaScript para leitura de fichas e fontes; filtros e rotação diária dependem de JavaScript. Abrir por HTTP permite também testar o histórico e os endereços compartilháveis.

## Reconstruir e testar

```powershell
py tools/sp/round_c/build.py
py -m pip install beautifulsoup4==4.13.4 playwright==1.55.0
py -m unittest discover -s tests/sp/round_c -p test_product.py -v
node --test tests/sp/round_c/test_filters.cjs
py -m playwright install chromium
py tests/sp/round_c/browser.py
```

No Linux, substituir `py` por `python`. O teste de isolamento precisa do histórico Git com os commits de referência; em um ZIP sem `.git`, usar o checkout do repositório para executar esses testes. A página pronta em `sp/` não precisa de Git para funcionar.

## Filtros

Os parâmetros são `q`, `partidos`, `pautas`, `modo`, `situacao` e `ordem`. Exemplo:

```text
/sp/deputados-federais/?partidos=PT,PSOL&pautas=educacao,saude&modo=todos
```

Partidos são combinados por união. Temas podem usar união (`modo=qualquer`) ou interseção (`modo=todos`). Busca, partidos, situação e temas são combinados entre si. O botão de compartilhar gera o endereço correspondente. Um link individual de ficha usa `#candidato-ID` e não carrega filtros que poderiam ocultar aquela ficha.

As categorias são **temas documentados**, não uma declaração de apoio genérico. Tocar no tema da ficha abre as afirmações correspondentes e suas fontes. Tipo de documento, temporalidade e direção da afirmação permanecem visíveis.

A ordem padrão é alfabética com deslocamento diário, no horário de Brasília. Também há ordem alfabética fixa. Não há pontuação ou preferência política na ordenação.

## Entradas e saídas

- `data/sp/research/`: pesquisa editorial congelada do Round B.
- `data/sp/round-b/`: cadastro técnico, fotos, biografias atribuídas e histórico.
- `config/party-scope-2026.json`: recorte canônico de 11 siglas.
- `config/topics-v1.json`: IDs e nomes nacionais, com a extensão documental de ciência/tecnologia já existente no Round B.
- `data/sp/round-c/`: dados complementares dos 15 registros adicionados e dataset do produto.
- `sp/deputados-federais/`: HTML, CSS, JavaScript, fotos e exportações públicas.
- `docs/sp/round-c/`: cobertura, checagem de disponibilidade, testes, capturas e validação.

A coleta complementar é um comando separado, `python tools/sp/round_c/collect.py`; ela usa a coleta congelada se `collection.json` já existe. Não remover fontes congeladas para simular uma atualização. Uma nova fotografia exige revisão explícita, comparação e novo versionamento.

## Pages e VPS

Os caminhos internos são relativos e foram testados tanto em `/esquerda-em-foco/sp/deputados-federais/` como em `/sp/deputados-federais/` em um servidor HTTP local. O endereço canônico padrão é o GitHub Pages do projeto.

Para gerar os endereços canônicos de SP em um domínio diferente:

```powershell
$env:EEFOCO_SITE_URL = "https://seu-dominio.example/"
py tools/sp/round_c/build.py
```

Isso não migra automaticamente os endereços canônicos das outras edições. A configuração global de domínio deve ser tratada no deploy do site inteiro.

## Integração segura

Não substituir a `main` pelo ZIP da branch: outras frentes continuam avançando. Integrar pelo PR, preservando os commits mais recentes de SC/RS/PR. O baseline testado nesta etapa é `89092b6192f5b06acba3fcb1ac7adef1af99b266`; a `main` recebeu alterações posteriores durante a execução.

As mudanças intencionais fora de SP são somente um link delimitado na navegação de `index.html` e duas entradas de São Paulo no `sitemap.xml`. Nenhuma edição de outro estado foi reescrita pelo build de SP.

**Não houve merge em main nem deploy nesta execução.**

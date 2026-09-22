# GLOBAL-02 · rotas e compatibilidade

## Contrato de implantação

GitHub Pages serve arquivos estáticos: a solução não depende de rewrites de SPA,
redirecionamento por fragmento no servidor ou endpoints novos. O fragmento `#...`
não é enviado na requisição HTTP. Por isso a compatibilidade é resolvida no
navegador e mantém acesso alternativo sem JavaScript.

Fontes técnicas: documentação GitHub Pages, “What is GitHub Pages”,
https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages ;
MDN, “URI fragment”, https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Fragment ;
MDN, “popstate”, https://developer.mozilla.org/en-US/docs/Web/API/Window/popstate_event .

## Migração por fases

| Hoje | Destino após #42 | Tratamento |
|---|---|---|
| `/` (SC/Federais) | `/sc/deputados-federais/` | Raiz sem fragmento passa a ser home; fragmentos SC conhecidos têm ponte |
| `/deputados-estaduais/` | `/sc/deputados-estaduais/` | Alias conserva query e fragmento |
| `/rs/deputados-federais/` | Mesma rota | Sem redirecionamento |
| `/pr/deputados-federais/` | Mesma rota | Sem redirecionamento |
| `/pr/deputados-estaduais/` | Mesma rota | Sem redirecionamento |
| `/sp/deputados-federais/` | Mesma rota | Sem redirecionamento |

Nesta etapa, as URLs públicas não são movidas. O ensaio é produzido fora do
repositório e inclui destinos reais clonados, ponte, alias, quatro hubs mínimos,
404 e navegação. Não é o desenho final da home.

## Ponte SC

`config/legacy-sc-links.json` congela os IDs efetivos da raiz auditada: fichas,
partidos, fontes e seções. `legacyRootTarget` aceita somente esses alvos ou uma
coleção SC válida. Rejeita valores inválidos, edição estrangeira, IDs desconhecidos,
duplicações e fragmentos excessivos. O destino é fixo na base validada, sem
redirecionamento aberto. Novas âncoras da home devem usar `global-*`, sem colisão
com a allowlist.

A coleção v1 `#selecionados=...&v=1&edicao=sc-federais&ficha=...` é preservada
integralmente e reaberta pelo leitor existente na rota nova. O contrato de novos
links v2 inclui ano/edição, mas não substitui o leitor antigo automaticamente.
Sem JavaScript a home oferece link explícito para SC; não promete reconstruir
fragmentos no servidor. Um link antigo contendo só a raiz, sem fragmento, é
indistinguível de uma visita à home: esse limite é intencional e explícito.

Base de implantação obrigatória: URL absoluta HTTP(S), sem usuário, senha, query
ou fragmento, com caminho seguro terminado em `/`. Testes cobrem raiz e
`/esquerda-em-foco/`. Links relativos de assets são recalculados ao clonar páginas;
âncoras e texto das fichas são conferidos, IDs não são duplicados.

## SEO

A correção atual do sitemap publica oito rotas já existentes. Não inclui as rotas
SC futuras ou RS/Estaduais em branch. `sitemap-next.xml` tem onze destinos para a
fase da home, sem aliases duplicados. O ensaio é `noindex,nofollow` e tem robots
com bloqueio geral; não deve ser confundido com o pacote de produção. A #42 deve
ativar canonical, robots, metadados, JSON-LD e sitemap de produção no mesmo commit
que ativar as rotas, validando o endereço servido antes de encerrar a entrega.

## Pendência não escondida

O motor SP existente ainda pode manter uma ficha oculta ao receber nova âncora
após uma busca. O ensaio testa a nova navegação, não declara essa falha local
corrigida. Transporte para #43/#44 permanece obrigatório.

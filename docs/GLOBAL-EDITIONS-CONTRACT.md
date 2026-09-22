# GLOBAL-02 · catálogo de edições e capacidades

Referências: issues #39, #41; auditoria #40 / PR #45. Baseline de implementação:
`cb845fcfb0b57f7907fd9d129555b6bb558a9ce1`.

## Estado desta etapa

Esta fundação não substitui a home pública. `root_mode=sc_federal_until_global03`
significa que a raiz ainda é SC/Federais. O catálogo descreve seis edições
publicadas e RS/Estaduais em branch. Não existe entrada fictícia SP/Estaduais.
O shell e as rotas futuras são executáveis num ensaio isolado, com `noindex`.
A integração visual pública e sua conferência HTTP pertencem à #42/#44.

## Fonte única

`config/editions.json` tem schema em `config/editions.schema.json` e validação
semântica complementar em `tools/global02/core.py`.

Cada identidade é `ano-uf-cargo`, por exemplo `2026-sc-federais`. `legacy_ids`
reconhece a identidade antiga sem permitir misturar anos. A candidatura tem chave
composta `edition_id:candidate_id`; o identificador não muda na fonte original.

Três eixos independentes:

- `publication_status`: publicado, somente branch ou arquivado;
- `research.status`: cobertura parcial, não iniciada ou escopo revisto;
- `capabilities`: disponibilidade técnica/documental de cada recurso.

`ready` descreve o recurso legado que realmente funciona na edição. Não significa
que recebeu o novo motor global. `global_shell` permanece ausente nas páginas
públicas enquanto só existe no ensaio. `blocked_data` não equivale a ausência de
posição da candidatura. O catálogo não contém seleção do visitante ou preferências.

`current_path` resolve a publicação de hoje; `canonical_path` é o destino do plano
de migração. `migration.routes_active` e `shell_active` impedem confundir projeto
com entrega. `snapshot` identifica o HTML auditado por ref/hash, não uma nova
consulta eleitoral. Datas de cadastro continuam nas fontes próprias, sem serem
substituídas pela data desta integração.

## Uso

```bash
python tools/global02/prepare.py --freeze
node --test tests/global02/core.test.cjs
python tests/global02/validate.py --out /tmp/global02-checks --rs-root /tmp/rs-branch
python tests/global02/rebuild.py --out /tmp/global02-rebuild
python tools/global02/build.py --out /tmp/global02-preview --base http://localhost:8000/
```

A preparação é um bootstrap da referência auditada, não um sincronizador de
pesquisa. Recusa outra raiz e valida hashes dos templates congelados. Depois da
migração #42, editar deliberadamente o catálogo; não voltar a gerá-lo a partir da
auditoria antiga. Nenhum build normal precisa acessar GitHub ou TSE.

`hub_data`, `shell`, `metadata` e `sitemap` derivam do mesmo catálogo. O shell é
HTML estático com links e `details`, utilizável sem JavaScript. O script acrescenta
Escape e retorno do foco; não carrega dados políticos nem faz telemetria.
Hubs inexistentes não recebem links na fase atual; o ensaio futuro gera quatro.

## Critérios de adoção

O catálogo, os templates independentes e a compatibilidade devem passar antes da
#42 trocar a raiz. A ativação de filtros e Selecionados em cada edição continua
na #43; não é requisito artificial para publicar a home. RS/Estaduais mantém os
gates editoriais e eleitorais próprios do PR #9. Uma ref auditada dessa branch
não autoriza sua publicação nem encerra a pesquisa.

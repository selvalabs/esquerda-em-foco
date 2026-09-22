# GLOBAL-03 · home, hubs e navegação

Issue #42; PR #47; epic #39. Baseline: `4d6ea9847f59fc6dfd52d57601b0ab19c8d3ecab`.
Estado de liberação e evidências: PR #47 e issue #42. A existência deste documento não significa que o deploy já foi verificado.

## Produto e escopo

A raiz torna-se a entrada geral: apresentação, quatro estados com acesso direto aos cargos disponíveis, leitura explicativa, critérios, fontes e limites da pesquisa. Quatro hubs mantêm contexto por estado. O seletor nativo de edições acompanha as seis páginas de consulta e é derivado de `config/editions.json`.

A identidade visual conserva o caderno editorial: fundo papel, tipografia serifada e os acentos verde, rosa e azul já usados no projeto. A home não utiliza fontes remotas, fotos de candidaturas, rankings, pontuações ou recomendações. A ordem dos estados na home é alfabética.

Seis edições estão disponíveis; RS/Estaduais continua em preparação e sem link público. SP/Estaduais não é inventada. Datas e cobertura próprias de cada edição não são redatadas pela atualização de navegação. O conteúdo dos 760 registros públicos é preservado, com identidade/texto, atributos das fichas e fontes externas verificados contra o baseline.

## Rotas

- Raiz: home geral.
- Hubs: `/sc/`, `/rs/`, `/pr/`, `/sp/`.
- SC: `/sc/deputados-federais/` e `/sc/deputados-estaduais/`.
- RS, PR e SP: endereços de cargo já existentes permanecem.
- `/deputados-estaduais/`: alias sem indexação, preservando query e fragmento; acesso explícito quando JavaScript estiver desligado.

A raiz reconhece somente fragmentos SC presentes em `config/legacy-sc-links.json` ou coleções SC v1 válidas. Novas âncoras usam `global-*`. Sem fragmento, a raiz abre a home. Um link antigo só à raiz é indistinguível de uma nova visita; o acesso direto a SC permanece disponível na home.

O fragmento não é redirecionado pelo servidor. A ponte usa destino fixo na mesma base. O projeto continua estático e não exige rewrites. Links novos da coleção SC usam sua rota canônica; a função de compartilhamento já existente não é duplicada.

## Navegação

O menu de edições usa links nativos e `details`; continua utilizável sem JavaScript. O script acrescenta Escape, devolução de foco, fechamento externo e exclusão mútua com o menu local. O menu local mantém as funções específicas da edição. O antigo link Início passou a Topo da edição; a marca leva à home geral. Uma trilha de localização explicita estado e cargo.

As melhorias de filtros, estrutura editorial e Selecionados nas outras interfaces ainda pertencem à #43. Não confundir a navegação integrada com paridade funcional. O finding SP de ficha oculta ao mudar a âncora após busca continua na #43/#44.

## Compilação e manutenção

`python tools/global03/activate.py` prepara a migração de fase e chama o builder. Após a migração, builds seguintes usam as páginas atuais, não restauram uma versão antiga da pesquisa e devem ser idempotentes.

Não executar o bootstrap `tools/global02/prepare.py --freeze` para sincronizar uma home já migrada: ele exige a raiz histórica e pertence à preparação anterior.

Os geradores legados continuam com seus templates independentes. Depois de gerar/revisar uma página, reaplique a camada global antes de integrar:

```bash
python tools/global03/refresh.py --edition 2026-sc-estaduais --input deputados-estaduais/index.html --source-path deputados-estaduais/index.html
python tools/global03/refresh.py --edition 2026-rs-federais --input rs/deputados-federais/index.html --source-path rs/deputados-federais/index.html
python tools/global03/refresh.py --edition 2026-pr-federais --input pr/deputados-federais/index.html --source-path pr/deputados-federais/index.html
python tools/global03/refresh.py --edition 2026-pr-estaduais --input pr/deputados-estaduais/index.html --source-path pr/deputados-estaduais/index.html
```

O adaptador estadual repõe também o alias. Fazer isso dentro do round editorial, antes de sua validação/publicação. Não integrar um build legado isoladamente: ele pode restaurar uma navegação antiga. Alterações legítimas de dados exigem um baseline novo, sem relaxar testes para aceitar regressões. A suíte `tests/global03/rebuild.py` exerce esse processo em worktree descartável, preservando a home.

## SEO e publicação

Sitemap gerado do catálogo com 11 destinos canônicos, sem alias duplicado nem branch publicada. Canonical, OG, JSON-LD e breadcrumbs acompanham as novas rotas. O cartão OG é gerado por `tools/global03/og.py`, com fontes locais e sem distribuir arquivos de fontes. A página 404 usa base absoluta para funcionar também em caminhos inexistentes aninhados.

`tools/global03/publication.py --prepare` congela hashes dos arquivos de publicação; sem esse parâmetro, confere bytes públicos e a resposta real de 404. O workflow de publicação também abre as páginas e reconstrói a coleção em navegador. Só encerrar #42 depois dessa conferência, não apenas após um merge.

## Validação e limitações

Testes de contrato, paridade, links/anchors, SEO, menus, busca/limpeza, coleções, teclado/foco e ausência de overflow. Navegador nos mounts raiz e Pages, em 320/360/390/430/768/1024/1440. Publicação checada em 390/1440. Não afirmar conformidade integral WCAG, aparelho físico, leitor de tela, nova coleta eleitoral ou envio de WhatsApp.

Na primeira execução, a contagem de links ignorou o endereço relativo `./` da própria edição. O teste passou a conferir os seis destinos absolutos, preservando o requisito. Uma interação sintética usada para fechar o menu local foi isolada dos eventos externos do seletor global. As falhas e correções ficam no histórico; reexecuções não são somadas como testes independentes.

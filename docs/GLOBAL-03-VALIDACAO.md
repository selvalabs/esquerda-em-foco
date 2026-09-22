# GLOBAL-03 · validação da implementação

A liberação final, o merge e a conferência pública ficam registrados na issue #42 e no PR #47. Este relatório preserva a proveniência da execução de implementação e não antecipa a publicação.

## Implementação aprovada

Baseline: `4d6ea9847f59fc6dfd52d57601b0ab19c8d3ecab`.
Código efetivamente executado: `8bb612fdf80960e8d260a5670a7bcb23925ba2a4`.
Run: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35760402519
Artefato: `10710002620`, SHA-256 `dc23544024435e2095255e59ca7688a42a7ce46554e1df49c44585f0980464dc`.

- 34 testes de contratos e 47 de regressão preexistente aprovados, sem falhas ou skips.
- 2.288 verificações de preservação, rotas, SEO e navegador aprovadas. Incluem hashes de 1.660 arquivos preexistentes: não são 2.288 funcionalidades independentes.
- 2.036 referências internas a arquivos/âncoras resolvidas; esse conjunto é uma verificação da suíte, não uma contagem adicional de testes.
- 18 verificações de reconstrução/adaptação dos geradores aprovadas.
- Segundo build sem alteração de bytes, árvore limpa.

As 760 fichas das seis edições preservam identidade, texto, atributos de dados e referências externas. Scripts de aplicação e payloads JSON das edições não foram alterados. Os snapshots e estados de pesquisa mantêm a proveniência anterior.

## Navegador

Onze páginas canônicas — home, quatro hubs e seis edições — testadas em 320/360/390/430/768/1024/1440, nos mounts `/` e `/esquerda-em-foco/`. Busca/limpeza, alternância entre menus, navegação por estado/cargo, Escape/foco e fallback sem JavaScript verificados.

Links antigos de SC foram exercitados com fichas, partidos, fontes/seções, coleção v1 e alias estadual. A coleção foi reconstruída em contexto novo de navegador preservando a ficha ativa. O novo compartilhamento aponta à rota canônica; o link WhatsApp foi conferido sem enviar mensagem.

A inspeção visual usou as capturas reais da execução: home desktop/mobile, seis edições mobile e hubs. Um ajuste posterior mantém a quebra de linha da nota introdutória no mobile, evitando juntar o ponto final ao link seguinte. Esse ajuste deve passar novamente pela validação de liberação; seus resultados não são atribuídos ao run acima.

## Reconstrução e limites

SC Estadual, RS Federal e PR Federal/Estadual foram reconstruídos em worktree descartável com os templates independentes. A camada global foi reaplicada e conferida, sem perder a home ou sobrescrever o alias. RS Estadual não foi publicado. O processo de manutenção está em `docs/GLOBAL-03-HOME.md`.

A primeira tentativa `35759566817` falhou no teste que contava links por substring e ignorava `./`, endereço válido da própria edição. O teste agora confere os seis destinos resolvidos. Também foi isolado o clique sintético de fechamento do menu local para não fechar indevidamente o seletor global. A tentativa falha não foi publicada nem contabilizada como aprovação.

Fotos externas foram bloqueadas nos testes de navegador. Não houve pesquisa política nova, coleta TSE, teste em aparelho físico, leitor de tela real ou envio de WhatsApp. A falha SP de ficha oculta após busca/hash permanece na #43/#44. A execução acima é do artefato da branch, não inspeção HTTP pública. A verificação pública tem workflow próprio e deve preceder o encerramento da #42.

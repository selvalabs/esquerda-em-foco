# GLOBAL-05 — publicação e gate final

Issue #44 · epic #39.

## Estado do candidato

O candidato GLOBAL-05 foi validado em CI remoto antes do merge. Baseline: `4a3300005fafbf85e13c4a61e763db1496924348`.

Run de QA candidato: **35890456988**, success. Artefato **10764579302**, SHA-256 `3d94896d907d26a8d2586efcee6247b52720d6825dae50e8f47923ce08dab994`.

Regressão D4 independente: **35890456936**, success. Artefato **10764952087**, SHA-256 `a941c3036bde034cbf7b88f225a70bf74bf3032892bf235edd00a23ff2fc814b`.

A comparação do head validado com o merge candidate mostrou zero diferenças de arquivos antes desta atualização documental. O novo head deve repetir o gate GLOBAL-05; alterações de produto não serão aceitas sem nova validação.

## Sequência obrigatória de liberação

1. Renovar o `main` e confirmar que pesquisas editoriais paralelas continuam independentes.
2. Exigir CI candidato verde e conferir o merge candidate.
3. Integrar somente o head aprovado.
4. Esperar o GitHub Pages publicar o merge.
5. Verificar o manifesto por **HTTP 200 + SHA-256**, além de uma URL inexistente com status 404.
6. Executar GLOBAL-05 direcionado, rollout amplo, Selecionados e verificadores SC/SP contra o domínio público.
7. Conferir titles/canonical/OG image no HTML servido.
8. Registrar run, commit, artifact SHA e horário da conferência na #44/PR.
9. Somente então encerrar #44 e o epic #39.

## Gate público automatizado

O workflow `.github/workflows/global05-public.yml` executa no `main`:
- `tools/global03/publication.py --out ...` para aguardar Pages e verificar todos os arquivos do manifesto e 404 real;
- `tests/global05/browser.py --base-url https://selvalabs.github.io/esquerda-em-foco/`;
- regressão pública do rollout;
- Selecionados e casos adicionais;
- verificadores públicos SC/SP;
- spot checks de title, canonical e imagem OG.

Os resultados pós-merge, por definição ainda desconhecidos neste documento de candidato, devem ser registrados como evidência final na issue/PR. **Um merge sem esse gate verde não encerra a #44.**

## Robots e sitemap

O sitemap é comparado às 11 rotas indexáveis do catálogo. O arquivo `/esquerda-em-foco/robots.txt` é servido dentro do projeto; diretivas de crawler para o host `selvalabs.github.io` são obtidas na raiz do host, portanto não se afirma que o arquivo do subdiretório controla o host inteiro.

Canonical e Open Graph são verificados no HTML servido, mas isso não comprova indexação, ranking ou renderização de preview por terceiros.

## Compartilhamento e acessibilidade

O QA verifica composição/reconstrução de links, dialogs, foco e estados de interface. Não envia mensagens reais, não aciona compartilhamento nativo do sistema operacional e não constitui auditoria integral de WCAG/leitor de tela/aparelho físico.

## Rollback

Guardar baseline, head aprovado, merge e artefatos. Em caso de regressão pública, revisar um revert do commit de integração e repetir o gate completo. Não executar rollback automático que possa sobrescrever pesquisa posterior.

## Fechamento

A #44 fecha somente depois de a versão publicada corresponder ao merge aprovado e os testes públicos terminarem verdes. O epic #39 fecha em seguida, confirmando que issues editoriais independentes preservam seus próprios estados. A #50 continua fora deste escopo.

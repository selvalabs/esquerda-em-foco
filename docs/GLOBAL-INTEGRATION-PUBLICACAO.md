# GLOBAL-05 — gate de publicação

**Estado deste pacote: não publicado.** A última versão remota verificada pelo conector durante esta revisão é `4a3300005fafbf85e13c4a61e763db1496924348`. Os resultados de publicação das etapas anteriores não são apresentados como aprovação das correções deste patch.

## Sequência de liberação

1. Confirmar o main vigente e a situação das frentes editoriais paralelas. O aplicador incluído no pacote recusa uma base diferente, uma árvore suja ou um patch incompatível. Não sobrepor o snapshot a pesquisas mais novas.
2. Aplicar o patch em branch isolada e verificar `git diff`. Não há alterações intencionais de conteúdo político, dados eleitorais, datas de pesquisa, taxonomia ou escolhas persistentes.
3. Executar a suíte GLOBAL-05 e as regressões por HTTP em ambiente autorizado, incluindo home/hubs, links de fichas, query v2, aliases/v1, Selecionados, fontes e navegação entre documentos. O workflow do pacote é uma configuração proposta, não uma execução já aprovada.
4. Conferir o commit efetivamente testado e o merge candidato. Depois de integrar, esperar a execução real do Pages e verificar o publicado; não fechar a issue apenas pelo merge.
5. Somente após os resultados públicos satisfazerem o escopo da #44, registrar os limites restantes e avaliar o fechamento da #44 e do epic #39. Não encerrar pesquisas independentes nem antecipar a #50.

## Verificação pública obrigatória

```bash
python tools/global03/publication.py --out /caminho/resultados/http-publico
python tests/global05/browser.py --base-url https://selvalabs.github.io/esquerda-em-foco/ --out /caminho/resultados/browser-publico
python tests/global_rollout/browser.py --live-base https://selvalabs.github.io/esquerda-em-foco/ --out /caminho/resultados/rollout-publico
python tests/global04/validate.py --live-base https://selvalabs.github.io/esquerda-em-foco/ --out /caminho/resultados/selecionados-publico
```

Conferir também os verificadores SC/SP e home existentes, a página 404 com **status HTTP 404**, aliases sem loops e links antigos abertos em documento novo. A existência de `404.html` não comprova o status servido. Checar os 41 arquivos do manifesto atualizado por HTTP/SHA-256; igualdade de arquivo local não comprova publicação.

## Robots e escopo do host

O arquivo versionado está em `/esquerda-em-foco/robots.txt`. Diretivas de rastreamento são obtidas na **raiz do host** (`https://selvalabs.github.io/robots.txt`), não arbitrariamente em um subdiretório de projeto. Portanto, a revisão local não declara que o arquivo do projeto controla os robôs no host. Confirmar a configuração do site de usuário/organização ou domínio próprio, conforme a infraestrutura efetiva. O patch não modifica outro repositório ou domínio.

O sitemap local é coerente com os 11 endereços indexáveis do catálogo. Isso não comprova descoberta, indexação ou posicionamento por buscadores. Canonical e metadados de compartilhamento devem ser conferidos no HTML servido, e a imagem Open Graph deve responder publicamente no endereço declarado.

## Compartilhamento e acessibilidade

Validar que o link de consulta ou coleção recompõe o estado em outra página/navegador, sem enviar mensagens reais por conta do usuário. O ensaio offline não pode validar URLs montadas a partir de `location.href` ou o compartilhador do sistema operacional.

Rever foco/Escape e as âncoras com cabeçalhos fixos também no documento carregado por HTTP. Capturas e ratios amostrados não equivalem a auditoria integral WCAG, leitor de tela ou aparelho físico. Registrar separadamente o que foi executado, não realizado ou ficou limitado.

## Rollback

O patch é reversível, mas não executar reversão automática em produção. Guardar a base, o commit aprovado e os artefatos. Se uma regressão publicada exigir retorno, revisar um revert do commit de integração e repetir o gate público, preservando pesquisas posteriores.

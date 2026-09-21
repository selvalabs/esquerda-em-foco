# São Paulo — Round C: entrega da interface

**Implementação e testes: PASS. PR de integração: aberto. Merge em main e publicação: não executados.**

Data da entrega: 21/09/2026. Repositório `selvalabs/esquerda-em-foco`, branch `feat/sp-federais-round-c`, issue #25, PR #31.

## Produto implementado

A edição está em `sp/deputados-federais/index.html`, com entrada em `sp/index.html`. Há busca por nome, número, partido ou conteúdo temático; filtros por várias siglas, situação no TSE e temas documentados; união ou interseção entre temas; contador de resultados; limpeza de filtros; endereços compartilháveis; links individuais de ficha; ordenação alfabética ou rotação diária explicada no horário de Brasília.

As fichas exibem foto, identidade eleitoral, situação do registro, afirmações documentadas, fontes, trajetória disponível, candidaturas anteriores e canais declarados. Tocar em um tema abre as afirmações que sustentam aquela associação. A interface distingue proposta, declaração e atuação; o filtro é por assunto documentado, não por apoio genérico a toda medida de uma categoria.

O HTML permite ler fichas e abrir as fontes sem JavaScript. Os filtros usam JavaScript local, sem depender de API, banco ou armazenamento de preferências. Há navegação por teclado, foco visível, disclosures nativos, redução de movimento, tratamento de foto quebrada e alternativa de cópia quando o clipboard não está disponível.

## Reconciliação de população e taxonomia

O Round B continha 234 registros nas oito siglas do recorte anterior. A configuração canônica recebida da main inclui 11 siglas: PCB, PCdoB, PCO, PDT, PSB, PSOL, PSTU, PT, PV, REDE e UP.

A página reúne **249 registros: 234 preservados + 10 da REDE + 5 do PSTU**. PCB permanece no filtro com contagem zero nesta fotografia. Os 15 registros adicionais receberam cadastro, situação, foto e canais a partir das fontes oficiais, mas **não receberam pesquisa temática individual ou pautas inferidas**. A inclusão de uma sigla no recorte não atribui posições aos seus candidatos.

A camada editorial foi importada, sem reescrever afirmações, do Round B: **42 fichas com temas documentados em 2026**, **218 associações candidato–tema** e **102 afirmações do período**. Outras dez afirmações — três históricas e sete sem data original confirmada — permanecem fora do filtro atual. Seis fichas têm apenas esse material não atual. As 186 fichas de B sem síntese e os 15 registros adicionais não são apresentados como contrários a qualquer pauta.

O produto inclui **249 fotos locais, 33 biografias atribuídas às respectivas fontes e 555 registros de candidaturas anteriores a 2026**. Histórico de candidatura não é contagem de mandatos. Votos históricos não coletados e votos/resultados do pleito de 2026 permanecem nulos, não zero.

A taxonomia mantém as 30 famílias documentais de B. Três IDs foram mapeados explicitamente para o contrato nacional: `apostas-protecao-economica` → `apostas-jogos`; `infraestrutura-desenvolvimento-regional` → `infraestrutura-desenvolvimento`; `povos-indigenas-comunidades-tradicionais` → `povos-indigenas-tradicionais`. A extensão documental de ciência/tecnologia já existente em B foi mantida. Nenhuma configuração ou associação de outros estados foi alterada para isso.

## Testes e verificação

A execução GitHub Actions **35646379842** passou em todas as etapas:

- **25 testes Python** de dados, HTML, referências, proteção dos arquivos e reconstrução determinística;
- **16 testes JavaScript** de filtros, URLs, aliases, temporalidade, busca e ordenação;
- **23 cenários Playwright/Chromium** em servidor HTTP real.

Os cenários incluíram larguras de 320, 390, 768 e 1.440 pixels; zoom CSS de 200%; teclado; navegação sem JavaScript; URL/reload/voltar/avançar; cópia alternativa; filtros combinados; registros de renúncia; histórico fora das tags atuais; carregamento dos 249 retratos; rotas com prefixo de GitHub Pages e na raiz de servidor; navegação pelas edições SC/RS/PR. Não houve erro JavaScript ou falha de asset local nos cenários de SP. As capturas estão em `screenshots/`.

O artefato foi baixado e revalidado fora do runner: **278 hashes conferidos**, **25 testes Python e 16 JavaScript repetidos**, reconstrução sem mudança nas saídas rastreadas e **856 caminhos preexistentes protegidos byte a byte**. O teste adicional de redimensionamento repetido com zoom confirmou a correção do cálculo de altura do cabeçalho. A inspeção local de layout usou conteúdo carregado em memória; os testes HTTP foram executados no GitHub Actions.

## Commits e evidências

- Código final testado: `61091d2d92719257f64f9b12e524d0856a5a7c42`.
- Produto gerado e testado: `90c4089e5e3d04bba2cda3f21e5c4b15e29c3d56`.
- Workflow: `35646379842`.
- Artefato: `10660510964`.
- SHA-256 do ZIP original do artefato: `9acb360ee1aa1fd62fa54fa648b85dff4a2af818e0ddf88c8c5200cea6fde46b`.

Os commits posteriores ao produto acima acrescentam documentação; não alteram o código ou a interface testados. O inventário original de 278 hashes cobre o artefato do workflow, não os documentos acrescentados depois. O pacote final para revisão tem inventário próprio.

Relatórios: `QA.json`, `build.json`, `browser-tests.json`, `unit-tests.txt`, `js-tests.txt`, `source-link-check.json`, `checksums.json` e `INDEPENDENT-VALIDATION.json`.

## Limites e pendências de conteúdo

O Round C não é uma nova auditoria factual de todas as afirmações políticas de B. Importa o material versionado e preserva autoria, temporalidade e fonte. Na verificação de disponibilidade, **61 das 75 URLs editoriais responderam e 14 falharam**. As falhas são sinalizadas nas fichas, sem apagar as referências anteriores. Resposta HTTP não comprova o conteúdo e falha de acesso não comprova inexistência da fonte.

Não houve visita individual a todos os perfis sociais. As 15 novas candidaturas do recorte ainda precisam de pesquisa temática. Lacunas biográficas, de cargos atuais e de votos históricos continuam identificadas. O cadastro é uma fotografia, não uma atualização em tempo real.

## Integração e publicação

O **PR #31 está aberto para revisão**, sem merge ou deploy por esta execução. Na consulta de encerramento, a API REST do GitHub informou `mergeable: true` e `mergeable_state: clean`; esse estado pode mudar se a main avançar novamente.

A main foi incorporada somente à branch C pelo PR #26. O baseline usado nos testes é `89092b6192f5b06acba3fcb1ac7adef1af99b266`. Outras frentes receberam commits posteriores durante o trabalho; a integração final deve preservá-los e repetir a verificação sobre o resultado do merge.

Fora dos caminhos de SP, as alterações intencionais são apenas um link delimitado na navegação da home e duas entradas no sitemap. **Não substituir a main pelo ZIP desta branch**: o pacote é uma fotografia de revisão, não um comando de publicação.

A reprodução local e os comandos de teste estão em `README.md`. A próxima operação é revisar e integrar o PR, verificar a versão resultante e então publicar, em uma etapa explicitamente autorizada.

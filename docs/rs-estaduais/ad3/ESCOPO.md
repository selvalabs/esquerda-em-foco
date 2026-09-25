# RS-EST-AD3 — Pesquisa substantiva das lacunas remanescentes

**Status:** escopo preparado; execução deste round ainda não iniciada.
**Data:** 22/09/2026.
**Repositório:** `selvalabs/esquerda-em-foco`.
**Issue existente:** #5. **PR existente:** #9.
**Branch:** `feat/rs-deputados-estaduais`.
**Baseline consultado para este escopo:** `181e927dfcc79a66d5e496be3b72d7f3017561c9`.

## 1. Objetivo e diferença em relação ao fechamento anterior

O AD2-CLOSE recuperou, reproduziu e organizou o trabalho já existente. O AD3 deve fazer pesquisa nova: ler fontes individuais, acrescentar sínteses quando sustentadas, esclarecer mandatos e atos e atacar as pendências nominais restantes. Não será outra rodada dedicada principalmente a reconstruir arquivos, testar disponibilidade de páginas ou renomear estados de pesquisa.

A meta de cobertura é percorrer as **88 candidaturas sem síntese**, com revisão individual verificável. Não há promessa de 88 sínteses novas: fontes podem ser insuficientes, inacessíveis ou não permitir conciliar a identidade. Nesses casos, registrar o resultado da busca e o próximo passo, sem afirmar que a candidatura não possui propostas.

A execução permanece na mesma issue, branch e PR. Não abrir nova issue para duplicar este trabalho. Não executar merge, deploy ou integração global.

## 2. Estado de partida confirmado

Fonte: `docs/rs-estaduais/ad2-close/report.json`, no baseline acima; a issue #5 e o PR #9 refletem esse fechamento.

| Indicador documental | Baseline |
|---|---:|
| Candidaturas no recorte | 149 |
| Sínteses temáticas existentes | 61 |
| Sem síntese temática | 88 |
| Pesquisa complementar pendente | 74 |
| Fontes consultadas insuficientes | 6 |
| Bloqueio ou falha de leitura registrados | 8 |
| Mandatos confirmados nas fontes preservadas | 16 |
| Fichas com atos institucionais | 31 |
| Atos institucionais registrados | 44 |
| Linhas históricas | 432 |
| Linhas com votação nominal conferida | 395 |
| Totais históricos ainda pendentes | 11 |
| Posições de vice/suplência sem voto nominal próprio | 26 |

Os grupos se sobrepõem; são métricas de documentação, não avaliações de candidatos.

A fila sem síntese distribui-se assim: **PDT 33, PSB 18, PT 16, PSOL 13, PV 4, PSTU 2, REDE 1 e UP 1**, totalizando 88. PCdoB não tem lacuna de síntese no baseline; isso não equivale a auditoria final das seis fichas. PCB e PCO pertencem ao critério, mas têm zero candidaturas neste snapshot.

A configuração canônica de onze siglas já foi reconciliada. Neste round, ela será somente lida. A população eleitoral permanece a do snapshot TSE de **21/09/2026 às 12:31:37** até a atualização prevista em F. Não confundir a data de nova pesquisa editorial com a data da consulta eleitoral.

## 3. Ordem e tarefas

### AD3-00 — Fixar a fila e preparar a integração incremental

- [ ] Ler o HEAD real no início da execução, conferir issue/PR e comparar com o baseline deste escopo. Preservar qualquer contribuição posterior; não sobrescrever concorrência.
- [ ] Recalcular as 88 lacunas por `SQ_CANDIDATO` e congelar uma fila nominal com nome de urna, partido, número, estado inicial, fontes já tentadas e próximo passo.
- [ ] Separar o processamento de novas evidências da reconstrução histórica do AD2-CLOSE. O workflow atual executa `close_ad2.py replay/probe/publish/report`; ele não deve reaplicar classificações antigas sobre conteúdo novo.
- [ ] Preservar os relatórios históricos e o vínculo ao commit que os produziu. Criar entradas incrementais para AD3; não substituir contadores antigos para fazer parecer que a versão anterior já continha o conteúdo novo.
- [ ] Ajustar apenas o código e os testes estritamente necessários para receber novas evidências, datas e estados. Testes fixos da recuperação devem continuar verificando a versão histórica correspondente, enquanto os testes do estado atual calculam os totais a partir dos dados.

**Aceite:** fila reproduzível e pipeline capaz de aplicar novas entradas sem apagar sínteses, duplicar atos, redatar fontes ou relaxar verificações de identidade. É uma preparação limitada, não uma refatoração geral.

### AD3-01 — Pesquisa nominal das 74 fichas pendentes

Para cada identidade da fila, executar uma pesquisa efetiva, não apenas gerar frases de busca. Aplicar o mesmo procedimento às 6 e às 8 fichas de AD3-02 após considerar as tentativas anteriores.

**Roteiro mínimo de investigação:**

1. Conferir os endereços individuais declarados e pesquisar site próprio, página individual partidária e plataforma/programa. Ler as fontes pertinentes que estiverem acessíveis.
2. Pesquisar nome de urna e nome civil, com partido e território quando necessário, procurando entrevistas ou declarações explícitas em veículos locais/regionais e publicações públicas identificáveis.
3. Quando houver indícios de trajetória institucional, consultar o órgão pertinente para fontes de mandato e atuação; quando não houver, registrar por que essa via não se aplica em vez de presumir ausência de experiência.

Um resultado útil não exige quantidade artificial de fontes: uma plataforma individual clara pode sustentar uma síntese. Contudo, declarar material insuficiente ou caso não resolvido exige documentar as vias pertinentes efetivamente examinadas, inclusive alternativas ao primeiro link indisponível. Contagem de buscas, HTTP 200, snippet isolado ou título de página não bastam para comprovar leitura.

- [ ] Registrar consulta executada, data, resultados pertinentes, URL tentada/lida, método de leitura, identidade conciliada, período, localizador, decisão e limitações.
- [ ] Preservar a diferença entre página da própria pessoa, entrevista, registro legislativo e notícia de gabinete.
- [ ] Produzir síntese autoral clara, sem slogans, superlativos ou redação promocional. Atribuir declarações ao candidato; não apresentá-las como resultado implantado.
- [ ] Não derivar pautas da profissão, da filiação, de biografia isolada, de hashtags, de preferências do visitante de um formulário ou de texto provisório.
- [ ] Identificar prioridades genéricas como prioridades genéricas, sem apresentá-las como programa detalhado. Uma manifestação antiga ou municipal, quando pertinente, deve conservar o período e o alcance; não vira automaticamente promessa estadual de 2026.

**Aceite:** cada ficha trabalhada possui evidência de pesquisa executada e um desfecho honesto. Uma nova síntese só conta após estar aplicada no dataset, visível na página e ligada à fonte individual.

### AD3-02 — Reabrir os 6 casos insuficientes e os 8 bloqueados

- [ ] Nos seis casos insuficientes, procurar fonte complementar especificamente voltada a propostas ou posições individuais; não repetir biografia ou notícia antiga como substituto.
- [ ] Nos oito casos bloqueados, registrar nova tentativa datada e buscar alternativa pública equivalente: outro endereço oficial, página individual do partido, entrevista, processo ou publicação acessível.
- [ ] Usar leitura em navegador ou documento público quando pertinente, sem contornar login, CAPTCHA, paywall ou restrição de acesso.
- [ ] Não transformar falha de um endereço em indisponibilidade permanente, nem em inexistência de propostas.
- [ ] Não duplicar a contagem quando a mesma pessoa tiver várias URLs ou mais de um motivo de dificuldade.

**Aceite:** tentativa anterior e nova tentativa permanecem auditáveis. Casos sem fonte suficiente continuam com lacuna fundamentada, não com síntese fabricada.

### AD3-03 — Mandatos e atuação vinculados à pesquisa

Este bloco complementa as pesquisas acima e resolve os indícios institucionais já conhecidos, inclusive de candidaturas com síntese existente.

- [ ] Criar uma fila objetiva de casos com indício de mandato atual ou anterior e de atos ainda incompletos. Priorizar a ALRS e, conforme o caso, câmaras municipais, prefeituras ou Câmara dos Deputados, sem conferir cargo por resultado eleitoral passado.
- [ ] Quando a fonte permitir, distinguir titular em exercício, suplente em exercício, suplente fora de exercício, licença, cargo executivo, mandato anterior e situação não confirmada. Data de consulta e período a que o documento se refere são campos diferentes.
- [ ] Registrar nova confirmação somente com fonte institucional suficiente para identidade, cargo e período. Preservar a data das 16 confirmações anteriores; elas não se tornam confirmações novas apenas por reaparecerem no build.
- [ ] Acrescentar atos verificáveis com tipo, autoria/coautoria/relatoria, número quando disponível, descrição factual, fonte e período. Diferenciar data do ato e publicação da notícia.
- [ ] Resolver o número da proposição municipal associada ao registro 331235 de Bruno Berté, já identificado como pendência, ou documentar precisamente por que não foi recuperado.
- [ ] Manter a distinção entre apresentado, aprovado, sancionado e executado. Um pronunciamento, relatoria ou voto isolado não sustenta automaticamente uma posição geral.

**Aceite:** novos cargos e atos têm confirmação primária compatível. Ausência de confirmação não significa ausência de mandato ou atuação. Cobertura ampliada é contabilizada separadamente de revisões de fontes já existentes.

### AD3-04 — Tratar os 11 totais históricos pendentes

- [ ] Partir da fila `ad2-close/historical-vote-pendencies.*`, separando os onze casos recuperáveis dos 26 de vice/suplência.
- [ ] Investigar cada pendência com a fonte compatível e conciliar ano, eleição, turno, cargo, UF/circunscrição, identificador, unidade eleitoral quando necessária e número. Nome civil é verificação complementar, não chave aproximada suficiente.
- [ ] Preservar as correções já auditadas de identificadores municipais e do recorte de 2010; não generalizar exceções a outras eleições.
- [ ] Para nova soma, guardar procedência, método e universo da agregação. O hash nacional só pode ser declarado quando todos os bytes nacionais tiverem sido lidos; hash de membro não é hash do ZIP inteiro.
- [ ] Publicar um total apenas com correspondência segura. Consulta a cadastro histórico não prova o número de votos. Sem fonte adequada, manter `null` e motivo explícito; nunca converter ausência em zero.

**Aceite:** os onze casos têm resultado de investigação ou pendência claramente registrada. Não prometer recuperar todos; não reclassificar vice/suplência como erro a preencher.

### AD3-05 — Aplicar as evidências e atualizar a página

- [ ] Integrar em lotes revisados, com identidade conferida, preservando fontes e histórico das versões anteriores.
- [ ] Separar `research_status` (qual evidência existe) de `review_completed_in_round` (o procedimento deste round foi efetivamente cumprido). Acrescentar um status a uma ficha não significa tê-la pesquisado.
- [ ] Manter os estados já usados: `policy_summary_verified`, `individual_sources_reviewed_insufficient`, `source_access_blocked`, `identity_ambiguity` e `research_pending`. Não promover pendência por simples passagem de tempo ou troca de rótulo.
- [ ] Versionar fonte, tipo de evidência, data de publicação quando conhecida, data de consulta, período do conteúdo, localizador, método de acesso, validação de identidade e decisão editorial. Hash somente quando os bytes correspondentes estiverem disponíveis; caso contrário, registrar a limitação.
- [ ] Corrigir texto anterior somente com evidência e nota de revisão. Não preservar afirmação errada para manter contagem, nem apagar texto válido por aplicação de `null` antigo.
- [ ] Regenerar página, dados, CSVs, fontes, cobertura e estados de pesquisa, mantendo linguagem legível e atribuições claras. Não redesenhar a interface.
- [ ] Usar uma data de corte explícita para a nova pesquisa. Não inserir fontes novas fingindo consulta em 21/09; manter separado o snapshot eleitoral preservado e a atualização editorial do AD3. Não admitir fonte com data futura sem esclarecimento.

**Aceite:** texto renderizado, dados normalizados, fontes, estados e relatórios concordam. Os totais são calculados dos registros, não digitados para atingir uma meta.

### AD3-06 — Regressão, isolamento e entrega

- [ ] Executar a suíte existente e os testes novos necessários, sem excluir ou pular testes apenas para produzir resultado verde. As 92 verificações unitárias e 63 de navegador são a referência anterior, não garantia de aprovação desta execução.
- [ ] Testar identidade, recorte, fontes, datas, atribuições, privacidade, contagens, votos e aplicação repetida dos lotes sem perda/duplicação. Qualquer correção legítima em dado anterior deve ter motivo e fonte.
- [ ] Testar busca, filtros, links profundos, históricos, retratos, fontes, downloads, teclado, notas da pesquisa, rotação e ausência de overflow nas larguras 320/360/390/768/1024/1440.
- [ ] Validar rebuild com fontes preservadas, sem exigir uma nova coleta externa em cada renderização. Conservar uma reconstrução auditável do fechamento anterior separada da edição nova.
- [ ] Comparar os caminhos protegidos contra o baseline da execução. Preservar demais estados/cargos, homepage, navegação global, servidor, assets compartilhados, sitemap global e configuração canônica.
- [ ] Gerar relatório antes/depois a partir do mesmo conjunto de IDs, vinculado ao SHA efetivamente validado; atualizar issue #5 e PR #9 com o resultado observado, mantendo ambos abertos.

**Aceite:** aprovação dos testes efetivamente executados, dados reprodutíveis, cobertura honesta e resultado versionado. Não declarar publicação com base em um workflow de build.

## 4. Organização da execução e proteção contra nova interrupção

A sequência é **00 → 01/02 → 03 → 04 → 05 → 06**. A confirmação institucional e a integração podem ocorrer junto de cada lote da pesquisa, sem esperar o fim da fila inteira.

Organizar as 88 identidades em lotes de até 12 fichas: sete lotes de 12 e um de quatro, recalculados caso o HEAD já tenha mudanças legítimas. Intercalar as siglas e trabalhar primeiro os casos ainda sem aprofundamento dentro de cada grupo, sem ordenar pela popularidade, potencial eleitoral ou suposta facilidade. A ordem de trabalho não altera a ordem pública de exposição.

Após cada lote, preservar as novas entradas revisadas e seu relatório. Usar uma única sequência de escrita na branch, evitando builds concorrentes que regravem outputs de estados diferentes. Não depender apenas de ZIP temporário ou de artefato com expiração. Em caso de interrupção, a fila deve indicar último lote validado, itens aplicados, itens apenas pesquisados e itens ainda não tratados. Não afirmar continuidade automática fora da execução.

## 5. Entregáveis previstos para o AD3

Os caminhos abaixo são saídas planejadas, não arquivos já produzidos pela execução:

- `docs/rs-estaduais/ad3/baseline.json` e `research-queue.json`: versão de origem, métricas e IDs da fila.
- `data/rs-estaduais/ad3/`: evidências individuais, alterações editoriais, fontes de mandato e atos, resolução de votos e decisões datadas, separadas das entradas históricas.
- `docs/rs-estaduais/ad3/batches/`: resultado e estado de integração dos lotes.
- `docs/rs-estaduais/ad3/candidate-coverage.json` e `.csv`: situação antes/depois, revisão cumprida, fontes e próximo passo de cada identidade.
- `docs/rs-estaduais/ad3/historical-vote-pendencies.*`: onze casos investigados e nulos justificados, separados das posições sem voto próprio.
- `docs/rs-estaduais/ad3/report.json` e `ENTREGA-AD3.md`: comparação calculada, testes, SHA, limitações e próximo gate.
- Página, exports e relatórios principais sincronizados, com indicação de onde estão os relatórios históricos de AD2-CLOSE.

Não exportar CPF, título eleitoral, endereço residencial, contatos privados, doadores, valores de contribuição ou reproduções extensas de conteúdo protegido.

## 6. Métricas e critérios para considerar o round concluído

**Cobertura de pesquisa:** 88 identidades no baseline; informar quantas tiveram procedimento cumprido com evidências, quantas tiveram somente tentativa parcial e quantas não foram tratadas. A soma deve fechar. O objetivo de revisão nominal integral é **88/88**, não 88 buscas escritas ou 88 testes de URL.

**Ganho editorial:** publicar o número de novas sínteses realmente acrescentadas às 61 existentes, a quantidade de correções/retrações justificadas, de lacunas insuficientes, bloqueadas ou de identidade e o saldo ainda pendente. Só criar novas sínteses se a evidência permitir; não há cota a preencher por invenção.

**Ganhos institucionais e históricos:** distinguir novas confirmações de mandato de meras releituras; novas fichas com atos de novos atos em fichas já cobertas; novos totais nominais de revalidações dos 395 anteriores. Medir também pendências resolvidas sem número quando a evidência demonstra que a classificação correta é outra.

**Gate de conclusão do AD3:**

1. Fila nominal integralmente revisada segundo o procedimento, com resultados e limitações auditáveis; impedimento de fonte pode continuar, mas o que não foi pesquisado permanece explicitamente pendente.
2. Toda nova síntese, afirmação institucional ou votação efetivamente publicada tem evidência compatível e identidade conciliada.
3. Todos os onze casos de voto e a fila institucional têm investigação ou impedimento registrado, sem chamar tentativa incompleta de conclusão.
4. Pipeline incremental não restaura estados antigos por cima de novos, e os relatórios históricos continuam reproduzíveis.
5. Página, exports e contadores correspondem ao mesmo estado validado, com testes de dados/interface/isolamento aprovados.
6. Resultados commitados e issue #5/PR #9 atualizados sem merge.

Se a pesquisa não alcançar a fila inteira, entregar o que foi validado e registrar **AD3 parcial**, com números e IDs restantes. Um novo relatório técnico verde, sozinho, não encerra o round substantivo. Se nenhuma síntese nova for sustentada, declarar ganho editorial zero e explicar os resultados da leitura, sem chamar reclassificação de enriquecimento.

## 7. Fora do escopo e próxima etapa

Não repetir recuperação de arquivos salvo nova evidência de problema; não refatorar genericamente o projeto; não alterar a seleção partidária ou os dados de outras frentes; não fazer redesign, nova rota, integração global, merge, deploy ou fechamento da issue #5.

A revisão editorial das novas entradas e os testes de regressão deste round **não equivalem a E/F concluídos**. E permanece a auditoria independente do conteúdo consolidado. F permanece a nova coleta TSE/DivulgaCand, o relatório de diferenças eleitorais e o gate de liberação. Uma mudança eleitoral percebida durante a pesquisa deve ser registrada para F, não incorporada silenciosamente ao snapshot antigo.

## 8. Referências do escopo

- Issue #5: https://github.com/selvalabs/esquerda-em-foco/issues/5
- PR #9: https://github.com/selvalabs/esquerda-em-foco/pull/9
- Baseline e métricas: https://github.com/selvalabs/esquerda-em-foco/blob/181e927dfcc79a66d5e496be3b72d7f3017561c9/docs/rs-estaduais/ad2-close/report.json
- Workflow de recuperação a separar do incremento: https://github.com/selvalabs/esquerda-em-foco/blob/181e927dfcc79a66d5e496be3b72d7f3017561c9/.github/workflows/rs-estaduais.yml

**Instrução de execução:** Execute o RS-EST-AD3 conforme `docs/rs-estaduais/ad3/ESCOPO.md`, na mesma branch, percorrendo a fila nominal de 88 lacunas, com lotes versionados, sem merge nem deploy. Relate somente ganhos e pendências efetivamente verificados.

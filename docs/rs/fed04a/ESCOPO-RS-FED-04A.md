# RS-FED-04A — pesquisa documental de 24 fichas e cinco históricos

## Estado desta preparação

Preparado em **22/09/2026**. **Pesquisa, alteração de conteúdo e publicação ainda não executadas nesta rodada.** Este documento delimita a próxima execução; não renova a data de conferência das candidaturas.

- Repositório: `selvalabs/esquerda-em-foco`.
- Issue de continuidade: #1, mantida aberta; não criar uma segunda issue para a mesma entrega.
- Branch de trabalho: `feat/rs-federais-fed04a`.
- Commit do main usado na preparação: `a815c909fa8551ed351e637ab0efb63390af6e19`.
- Manifesto: `data/rs/fed04a/targets.json`.
- Referência de cobertura: `docs/rs/fed03/final-report.json`, datada de 21/09/2026.
- Pendências e motivos anteriores: `docs/rs/fed03/README.md`, `research-log.json` e `candidate-matrix.json`.

A preparação acrescenta apenas este escopo e o manifesto. Não modifica a página publicada, os dados eleitorais de produção, o main, filtros ou workflows de pesquisa/deploy.

## 1. Objetivo e universo

Pesquisar individualmente **24 das 47 fichas ainda sem síntese de pautas/atuação** no relatório de referência. Resolver o que as fontes efetivamente permitirem e publicar os avanços após revisão e testes. As **23 outras fichas** ficam nominalmente reservadas para RS-FED-04B no mesmo manifesto.

O relatório RS-FED-03 registra 111 fichas, 64 com pautas/atuação, uma apenas com trajetória e 46 sem síntese suficiente. São indicadores históricos do projeto, não uma nova consulta eleitoral de 22/09/2026. Uma síntese existente não certifica completude de todos os campos.

As cinco pendências de votação nominal formam uma tarefa paralela delimitada. Não confundir essas cinco pendências com as cinco ausências já qualificadas por cadastro histórico inapto nem com os casos de vice/suplente sem votação nominal individual.

## 2. Seleção reproduzível do lote

**Primeiro bloco:** Daiane Martins, Ícaro Madalena, Julio Moura Voluntário e Marlise Janete. Essas quatro fichas foram incorporadas por correção do recorte durante a rodada anterior e receberam apenas triagem. Entram agora para receber o roteiro completo de pesquisa.

**Segundo bloco:** as primeiras 20 das outras 43 pendências, em ordem alfabética global do nome, sem agrupar por partido. Normalizar com Unicode NFD, casefold e remoção de marcas de acento; desempatar pelo ID TSE.

A divisão é operacional, não uma avaliação de candidaturas. Não muda a ordem pública de exposição nem atribui relevância eleitoral a quem é pesquisado primeiro.

O lote A terá: Aline Constantino Bento, Alisson Oliveira, Anelize Carriconde, Ary Vanazzi, Baiana Márcia França, Betina Torriani, Bruno Cardozo, Cida Brizola, Claudia Souza, Cleo Hickmann, Cleusa Zaikowski, Cris Machado, Duda Barin, Eduardo Manique, Elias Cabreira, Fortunati, Fufa, Gilberto Beltrame, Guido CNR e Ivan Braz, além das quatro fichas do primeiro bloco.

Todas as identidades, siglas e filas constam do manifesto. Não selecionar por expectativa de resultado, posição política ou facilidade de produzir texto.

## 3. Etapa A — reconciliar antes de pesquisar

1. Ler o HEAD atual do main e o estado desta branch/PR. Identificar mudanças posteriores à preparação, especialmente nos diretórios RS e na configuração canônica do recorte.
2. Recalcular os conjuntos a partir dos dados vigentes: população, fichas com pautas/atuação, somente trajetória, sem síntese e lacunas históricas. Comparar com o manifesto sem o sobrescrever silenciosamente.
3. Registrar adições, remoções ou fichas já tratadas por outra frente em um relatório de diferenças. Preservar os quatro registros incorporados na rodada anterior e a configuração compartilhada. Não forçar os números 111/47 se evidência nova justificar mudança.
4. Registrar o commit de integração de referência e hashes dos caminhos públicos das outras frentes. Não restaurar SC ou outro estado a um snapshot antigo para fazer um teste passar.
5. Congelar as entradas da execução e os indicadores antes/depois. Nenhuma coleta de rede deve ocorrer silenciosamente durante a renderização.

## 4. Etapa B — pesquisa das 24 fichas

Executar em seis blocos de quatro fichas, preservando o manifesto. Salvar fontes, decisões e alterações validadas ao concluir cada bloco; isso permite retomada sem perder trabalho. Os checkpoints são de versionamento, não promessa de execução autônoma em segundo plano.

### Roteiro por ficha

- Ler primeiro as consultas e limitações do RS-FED-03. Não repetir a mesma busca sem uma hipótese nova.
- Confirmar identidade por ID eleitoral e correspondências documentais, separando homônimos. Nome de urna, ocupação, cidade ou sigla isolados não bastam.
- Procurar fontes institucionais pertinentes: Câmara dos Deputados, ALRS, câmaras municipais, prefeituras, órgãos públicos, proposições e registros de autoria.
- Examinar site e canais individuais comprovados, página individual do partido, entrevistas originais e imprensa confiável quando necessário. Um programa genérico do partido não é uma fonte individual.
- Nas fontes audiovisuais, usar fala efetivamente acessível com localizador. Título, participação em evento, thumbnail, comentário de terceiro e trecho indexado sem contexto não justificam sozinhos uma proposta.
- Avaliar biografia, cargos, pautas e propostas em campos distintos. Não converter formação profissional, local de nascimento ou participação em atividade em pauta, vínculo territorial de atuação ou cargo atual.
- Redigir somente o que estiver sustentado; não impor tamanho mínimo nem preencher espaço com texto genérico.

### Registro de evidência

Cada afirmação nova deverá registrar: ID TSE, texto sustentado, URL, responsável pela fonte, data do documento quando disponível, data de acesso real, localizador (seção, página, artigo ou tempo de vídeo), natureza da informação e limitação de acesso. Identificar também as fontes rejeitadas e o motivo relevante, sem expor dados pessoais desnecessários.

Tipos de informação: proposta de campanha, declaração pública, proposição legislativa, atuação de gestão, realização comprovada, fato histórico e trajetória. Uma fonte institucional pode hospedar um texto de gabinete; nesse caso a declaração continua atribuída, não vira automaticamente verificação independente de execução.

Consultas previstas são plano. Só preencher o log de consultas executadas depois de realizá-las; resposta HTTP positiva comprova acesso, não comprova o conteúdo da ficha.

### Resultado por ficha

Registrar separadamente conclusão do roteiro e cobertura do conteúdo. Resultados possíveis: síntese de pautas/atuação sustentada, somente trajetória, informação insuficiente, fonte relevante inacessível ou conflito de identidade/fontes. Dizer o que permanece pendente e qual tentativa seguinte faz sentido.

Uma biografia, um aviso de lacuna ou uma pesquisa concluída não contam como nova síntese de pautas. Não chamar uma ficha de integralmente fechada por possuir apenas um desses campos.

## 5. Etapa C — cinco históricos nominais

Os localizadores constam de `vote_tasks` no manifesto:

- Claudia Souza: 2004 e 2008; buscar evidência adicional para os dois conflitos de identidade já registrados.
- Marlise Janete: 2018; reconciliar o registro incorporado ao recorte.
- Julio Moura Voluntário: 2022 e 2024; reconciliar os dois registros incorporados ao recorte.

Conferir ano, turno, cargo, localidade, ID histórico e nome civil nas fontes oficiais. Quando houver votação por município/zona, verificar o agregado correto e impedir soma duplicada de turnos ou localidades.

Uma exceção de identidade requer evidência documental específica e limitada ao registro, não uma regra geral de correspondência aproximada. Não atribuir votos a homônimo. Preservar a distinção entre zero verificado, valor indisponível, ausência de linha nominal, conflito de identidade e votação individual não aplicável.

Reexaminar os cinco casos já qualificados no RS-FED-03 somente se surgir evidência nova ou erro concreto. Não recategorizá-los artificialmente como pendentes ou resolvidos para alterar contadores.

Todos os cinco registros receberão uma decisão auditável nesta rodada; valor numérico novo só será publicado quando confirmado. Investigações sem resolução serão encaminhadas explicitamente à continuidade.

## 6. Etapa D — cargos, canais e dados eleitorais

Verificar cargos e canais das 24 fichas durante a mesma pesquisa. Cargo atual exige fonte institucional compatível com o período e identidade confirmada; resultado eleitoral ou biografia antiga não prova exercício atual. Não declarar inexistência de cargo por ausência em diretório.

Confirmar canais antes de corrigir endereços declarados. Registrar redirecionamento, DNS, remoção, bloqueio ou login exigido como situações distintas. Não adivinhar usernames nem publicar meios pessoais de contato desnecessários.

Reconsultar cadastro e situação nos arquivos oficiais antes da publicação. O bloqueio 403 anterior deve ser tratado como limitação de acesso: usar novas tentativas pontuais e limitadas; se persistir, registrar e manter os snapshots anteriores com suas datas, recorrendo aos arquivos oficiais acessíveis. Não repetir uma bateria de 111 acessos bloqueados nem contornar controles de acesso. Consulta a CSV não será relatada como reconferência de perfil individual.

## 7. Etapa E — integração sem regressões

Criar entradas próprias do round em `data/rs/fed04a/` e evidências em `docs/rs/fed04a/`. Integrar a nova camada documental ao mecanismo vigente antes de gerar `rs/deputados-federais/`. Não executar uma migração antiga isolada que apague as camadas RS-FED-02/03.

Preservar relatórios históricos, fontes anteriores válidas, os demais registros da base, fotos, URLs estáveis e ordenação pública. Dados gerados devem derivar das mesmas entradas validadas e produzir resultado determinístico. Correções do conteúdo anterior exigem motivo, fonte e registro de diferença.

Manter o vocabulário documental existente, com evidência por associação candidatura-tema e período explícito. Não implantar nova taxonomia compartilhada ou interface de filtros neste round. Meras palavras citadas na biografia, cadastro ou notícia não atribuem pauta.

Caminhos permitidos para a futura implementação: `data/rs/`, `docs/rs/`, `tools/rs/`, `tests/rs/`, `rs/deputados-federais/` e, se estritamente necessário, workflow exclusivo `rs-fed04a-*`. Não alterar SC, RS estadual, PR, SP, arquivos compartilhados de filtros, recorte canônico ou sitemap para concluir esta rodada.

## 8. Etapa F — revisão, testes e publicação

Revisar as 24 fichas alteradas e a coerência da base gerada inteira: fontes correspondentes, período, autoria, separação de proposta/execução, neutralidade e contadores. Evitar linguagem promocional, julgamentos, rankings, rótulos avaliativos ou previsões eleitorais.

Rodar as suítes pertinentes de dados/privacidade/fontes, recorte canônico e navegador existentes; acrescentar testes para novos casos. Os números anteriores (51 testes RS, três do recorte e 200 verificações de navegador) são referência de cobertura, não evidência de testes executados agora nem metas a atingir removendo verificações.

Cobrir larguras 320, 360, 390, 430, 768, 1024 e 1440; busca, menu, imagens, âncoras, históricos e ausência de overflow. Validar visualmente as fichas com textos ou notas novos. Repetir o build e comparar os quatro arquivos públicos principais. Não declarar reprodução ou QA bem-sucedidos sem executá-los.

Antes de integrar, conferir novamente main, PR, conflitos e arquivos alterados. Fazer merge somente com dados revisados e testes aprovados. Depois, confirmar o deploy e os bytes dos arquivos servidos; comparar a integração com seu pai real e verificar preservação das outras frentes. Se qualquer etapa falhar, registrar o resultado e não anunciar publicação concluída.

## 9. Critérios de conclusão e indicadores

O trabalho do lote A estará executado quando as 24 fichas e os cinco históricos tiverem decisões documentadas, as alterações sustentadas tiverem sido revisadas e os testes/publicação aplicáveis estiverem efetivamente verificados. Isso não exige nem autoriza inventar 24 novas sínteses.

Relatar: fichas pesquisadas; novas sínteses de pautas/atuação; fichas somente com trajetória; fontes inacessíveis; conflitos; cargos e canais comprovados; históricos resolvidos ou encaminhados; cobertura total antes/depois; e mudanças de universo.

Se a população e as 64 sínteses anteriores permanecerem iguais, a pendência final será `47 - novas_sinteses_de_pautas`, não automaticamente 23. Manter separadas as 23 fichas ainda não trabalhadas do lote B e eventuais pendências remanescentes do lote A.

A issue #1 não será encerrada automaticamente pelo PR. RS-FED-04B permanece uma execução própria; RS-FED-05 será a auditoria final. Qualquer encerramento deve refletir cobertura suficiente e pendências efetivamente resolvidas, não apenas o término de uma rodada.

## 10. Entregáveis da execução futura

Entradas documentais, log real por ficha, matriz antes/depois, decisões dos cinco históricos, registro de limitações, testes e QA, relatório de publicação, commit/PR e pacote reproduzível da frente RS sem arquivos de outras frentes. A nova data de revisão só deve ser aplicada aos dados de fato reconsultados; informar períodos diferentes quando necessário.

## Checklist operacional

- [x] Ler issue e relatórios existentes e fixar baseline da preparação.
- [x] Dividir as 47 lacunas em 24 alvos e 23 reservas, sem sobreposição.
- [x] Identificar os cinco históricos e preservar as decisões anteriores.
- [ ] Reconciliar com o main e com os dados vigentes na execução.
- [ ] Pesquisar as 24 fichas em seis blocos rastreáveis.
- [ ] Investigar os cinco históricos nominais.
- [ ] Conferir cargos/canais pertinentes e reconsultar cadastro oficial.
- [ ] Integrar fontes e textos, preservando rodadas anteriores.
- [ ] Revisar conteúdo e executar testes/QA/rebuild.
- [ ] Integrar, conferir publicação e atualizar issue com cobertura real.

**Princípio:** pesquisa registrada, conteúdo documentado e perfil completo são estados diferentes. Não convertê-los um no outro por conveniência de contagem.

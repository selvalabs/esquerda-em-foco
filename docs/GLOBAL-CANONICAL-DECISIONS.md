# GLOBAL-01 — decisões de canonização por composição

Issue #40 / epic #39. Decisões técnicas para #41–#44, derivadas da auditoria de 22/09/2026. **Não representam funcionalidades já aplicadas às outras edições.** Fontes: [auditoria](GLOBAL-CANONICAL-AUDIT.md), [matriz](../data/global-integration/capability-matrix.json) e [índice de evidências](../data/global-integration/evidence-index.json).

## D01 — Um produto, várias edições; nenhum estado como molde completo

**Decisão: adaptar por composição.** Preservar o vocabulário visual editorial existente — hierarquia tipográfica, mapa contextual, leitura e fontes — e extrair contratos/componentes por capacidade. SC fornece leitura e coleção; SC Estadual, cadastro/mandato; RS, história e pesquisa/correção; PR, filtros estruturados; SP, estado de consulta e evidência focalizada. Não importar uma pasta inteira como padrão global.

A arquitetura continua estática, com HTML legível sem JavaScript. Esta etapa não exige React, SPA, backend, conta de usuário ou reconstrução integral da stack. A separação entre dados, geração e comportamento é necessária; troca de framework não é critério de conclusão.

## D02 — Registry é metadado do produto, não cópia da pesquisa

**Decisão: criar `config/editions.json` na #41**, com schema validável e adapters próprios. Campos mínimos: versão, identificador estável, ano eleitoral, UF, cargo, título público, rota canônica, aliases, entrypoint, publicação, cobertura editorial, datas/snapshots e capabilities.

Manter três eixos independentes:

- `publication_status`: não criado, branch/preview, publicado, arquivado, conforme estados homologados;
- `research_status`: cobertura e pendências próprias da edição, com data e relatório;
- `capabilities`: cada recurso pronto, bloqueado por dados, não aplicável ou deliberadamente local.

A existência de código em branch não produz link público. A existência de uma ficha não significa pauta suficiente para filtros. As contagens da home vêm de manifests versionados de cada edição; não de números digitados à mão e não são soma nacional sem definição de população.

## D03 — Raiz geral, hubs e rotas simétricas com compatibilidade

**Decisão:** raiz para a home geral; hubs `/{uf}/`; edições `/{uf}/deputados-federais/` e `/{uf}/deputados-estaduais/` quando existirem. Manter RS, PR e SP nas rotas já compatíveis. Propor SC/Federais em `/sc/deputados-federais/` e SC/Estaduais em `/sc/deputados-estaduais/`, com compatibilidade de `/deputados-estaduais/`.

O ano integra a identidade dos dados, mesmo sem ser adicionado imediatamente à URL pública. O alias `sc-federais` do compartilhamento v1 continua vinculado à edição 2026; nunca passa silenciosamente a representar outra eleição.

**Gate de links legados:** a raiz sem fragmento vira home. Fragmentos SC conhecidos, incluindo `#candidato-...` e coleção v1, precisam ser identificados por allowlist e levados à nova edição preservando IDs, ordem e ficha ativa. Inventariar também âncoras antigas de partido, fontes e seções; reservar nomes distintos para os novos blocos da home. Não transportar fragmentos desconhecidos a destinos arbitrários nem aceitar URL externa como parâmetro de redirecionamento.

Fragmentos não chegam ao servidor. Por isso a compatibilidade da antiga raiz não pode depender somente de redirecionamento HTTP; a solução estática exige um pequeno resolvedor cliente e um caminho de acesso visível sem JavaScript. No Pages, não pressupor rewrites de servidor. Base path configurável deve funcionar sob `/esquerda-em-foco/` e na raiz de um domínio.

## D04 — Navegação global e contexto local coexistem

O shell apresenta Home, Estado, Cargo e edição ativa; breadcrumbs resolvem o mesmo catálogo. A navegação local continua oferecendo candidaturas, leitura, metodologia e fontes. Um link chamado Início não deve significar ora home global, ora topo da ficha sem distinção.

PR e SP fornecem o precedente de navegação entre edições, não os arrays hardcoded atuais. Não geolocalizar a pessoa para escolher estado automaticamente. Edições indisponíveis só aparecem como tal quando houver registro real no catálogo e mensagem honesta, sem link morto.

## D05 — Filtros combinados com semântica explícita

**Adotar/adaptar:** busca por termos normalizados e filtro efetivo de partidos de SP; combinações cadastrais, de mandato e trajetória de PR/SC Estadual; painel compacto e OR/AND de SC/SP.

Partidos selecionados formam união. Grupos temáticos usam Qualquer por padrão em consultas novas, com opção Todas. Importar o estado legado de PR preserva sua conjunção temática, em vez de reinterpretá-la silenciosamente. Busca apenas consulta campos previstos; não cria associações temáticas por palavras-chave. Filtro não altera ordem por afinidade.

Contagens devem indicar se são universo da edição ou resultado da consulta, sempre por IDs distintos. Ordenação diária determinística permanece disponível; ordem alfabética pode ser oferecida, como em SP. Quantidade de temas ou fontes nunca é critério de relevância.

## D06 — Não fundir apoio atual com documentação temática

**Adotar o rigor semântico de SC e a consulta documental de SP, sem equipará-los.** O contrato terá capacidades semanticamente distintas, por exemplo:

- `current_support`: apoio ou prioridade atual com atribuição, objeto, período e evidência suficiente;
- `documented_topic`: afirmação ou atuação documentada sobre o tema, mantendo natureza, direção e data visíveis.

Os rótulos públicos precisam dizer o que está sendo filtrado. Uma edição pode oferecer somente uma capacidade ou nenhuma. Um relato de atuação em 2026 não vira proposta de campanha apenas pelo ano; oposição não vira apoio a todo macrogrupo. Uma prioridade ampla explicitamente declarada não precisa virar projeto de lei detalhado para ser documentada como prioridade.

PR/RS legados sem metadados suficientes ficam como conteúdo contextual até haver associação revisada. A integração não está autorizada a fazer essa revisão por inferência. Campo ausente não equivale a opinião contrária.

## D07 — Taxonomia extensível, sem apagar contribuições das outras frentes

A estrutura SC de famílias e macrogrupos é a base de apresentação, **não a lista exaustiva de assuntos permitidos**. O produto SP já incorpora Ciência/Tecnologia além das 29 famílias. Catálogos de PR e RS contêm recortes próprios, inclusive conceitos que exigem exame específico de equivalência.

A #41 deve definir IDs, versões, aliases e registro de conceitos pendentes. A #43 só migra associação após validar se o conceito de destino preserva seu escopo. Nome igual pode esconder amplitude diferente; nome diferente pode ser alias legítimo. Não fazer classificação automática por keyword, nem propagar apoio a todas as famílias do mesmo grupo. Catálogo sem resultado permanece documentado; um botão vazio não precisa ocupar o painel público.

Esta auditoria **não homologou um crosswalk político completo de todas as associações**. Homologou a necessidade, a estrutura e os gates dessa adaptação. Isso não bloqueia catálogo de edições ou shell; bloqueia ativação indevida de filtros.

## D08 — Ficha e evidência com adapters, sem flattening destrutivo

A interface comum deve poder renderizar identificação/registro, mandato e trajetória, pautas atuais, outras posições, atuação registrada, fontes/contexto e estado da pesquisa, omitindo seções sem conteúdo.

O adapter deve manter os IDs de origem e expor, quando disponível, `claim_id`, candidatura, natureza, direção, objeto, tema, período, origem/atribuição, fonte, localizador, data de publicação e data de consulta. Não preencher desconhecidos com valores supostos. Não converter toda biografia em política pública ou toda fonte da ficha em fonte de todas as frases.

**Compor SC + SP:** explicação junto ao trecho e abertura focalizada das evidências do tema, com acesso ao contexto completo. Conservar o conteúdo estático no HTML e evitar duplicação das fichas entre lista e leitor.

## D09 — Cadastro, mandato, histórico e pesquisa são camadas diferentes

**Compor SC Estadual + RS + PR.** O contrato eleitoral conserva situação e snapshot. O de mandato distingue fonte institucional atual, licença, suplência, relato próprio e ausência de confirmação. O histórico usa chave contextual de eleição, território, cargo e turno quando pertinente; votação `null`, zero verificado e não aplicável não são intercambiáveis.

**Adotar o princípio de RS Estadual:** `research_status` não substitui `review_completed_in_round`. Uma consulta nominal, índice ou fonte bloqueada não encerra uma revisão. Correções mantêm antes/depois, motivo e fonte; não restaurar dados antigos durante rebuild. O componente pode ser reutilizado sem liberar a publicação da branch de origem.

## D10 — Selecionados pertence à edição; não é comparador avaliativo

**Adaptar o fluxo SC:** escolher vários registros, ordem de inserção, uma ficha por vez, Anterior/Próxima, remover, limpar com confirmação e voltar à lista. Não há seleção automática, ranking, pontuação, recomendação ou comparação competitiva. Não reintroduzir um comparador lado a lado como se tivesse sido a entrega aprovada.

A #41 define contrato parametrizado por edição, IDs e adapter de DOM. A #43 remove guards de 48 e edição fixa. Os limites de parsing/transporte têm de ser explícitos e defensivos, mas não podem truncar silenciosamente uma coleção ou impor um teto visual arbitrário. Testar 249 registros e catálogos maiores que os limites atuais antes de declarar o motor global.

Uma coleção não mistura cargos, estados ou anos automaticamente. Trocar de edição não importa preferências da anterior. O leitor usa o card original ou representação canônica sem IDs duplicados e preserva consulta/posição de retorno.

## D11 — Compartilhamento explícito, consulta em memória

**Compor restauração de SP/PR com privacidade do SC.** Padrão recomendado para a implementação global: consulta em memória durante o uso; ao compartilhar, gerar fragmento versionado com edição e somente os campos suportados. Manter importadores para URLs legadas PR/SP, saneando parâmetros desconhecidos e preservando sua semântica.

Não reproduzir a atualização automática de filtros sensíveis na query como padrão novo. Query e fragmento têm exposições diferentes; o link explícito também não é secreto, deve avisar a pessoa. Back/forward, abertura de ficha e restauração devem ter testes próprios e não apagar a consulta de forma inesperada.

Compartilhar ficha, consulta ou coleção precisa ser ação distinguível. A mensagem é descritiva, sem recomendação política; quem usa escolhe contato e confirma no aplicativo. Clipboard tem alternativa manual. Cancelar o compartilhamento nativo não dispara outro canal. O contador permanece desativado; nenhuma escolha é enviada a analytics, cookie, armazenamento local ou backend.

## D12 — Preservar estilo e responsividade, não acumular todas as barras

SC fornece a leitura editorial e o painel em diálogo; SP fornece resumo de consulta e filtros recolhíveis. O shell global deve escolher um contrato de breakpoints e tokens, mantendo um único conjunto de controles no DOM. Todos os controles de PR não devem virar uma faixa permanente que ocupe a tela mobile.

Acessibilidade é parte do contrato: foco visível, teclado, nomes acessíveis, Escape, retorno de foco, anúncios e leitura sem JavaScript. As medições desta auditoria não certificam WCAG integral. Não apagar conteúdo ou fonte para obter um screenshot mais limpo.

## D13 — Templates e rebuild antes da troca da raiz

**Não globalizar a dependência de páginas geradas como template.** SC Estadual lê a raiz atual; RS busca uma raiz histórica; PR e RS Estadual dependem do HTML pronto de RS Federal. A #41 deve inventariar cada entrada ativa, extrair moldes versionados e separar adapters de dados. As etapas históricas permanecem como proveniência, não como geradores que possam sobrescrever a UI atual.

Gate: mudar a home não muda a pesquisa, dados ou cards de uma edição; duas gerações iguais produzem bytes iguais; uma edição não precisa reconstruir outra para obter seu layout. Baseline deve ser reconciliado com o main efetivo antes de cada lote, sem restaurar arquivos alheios só para satisfazer hashes antigos.

## D14 — Home geral e hubs fazem parte do produto canônico

A #42 entrega apresentação curta do projeto, escolha de estado/cargo, disponibilidade real, explicação acessível de escopo/fontes/limitações e acesso à metodologia. Usar o catálogo para menu, hubs, breadcrumbs e metadados. Não anunciar um inventário de toda a esquerda brasileira a partir das edições disponíveis.

Na primeira home, a entrada é **por edição**, não uma busca nacional improvisada. Busca global exige contrato de identidade, índice e cobertura independente; não é gate deste round. Indicadores gerais só entram com população e data definidas. Os mapas são contexto visual, não seleção automática pela localização da pessoa.

## D15 — SEO, publicação e coisas que ficam de fora

Home, hubs e edições têm titles/descriptions/canonical/OG coerentes e URLs resolvidas pela mesma base. O sitemap principal precisa corresponder ao conjunto realmente indexável, incluindo as rotas publicadas omitidas hoje. Branches e aliases não viram duplicatas indexáveis. A 404 deve funcionar no Pages e em instalação na raiz.

Não globalizar: hardcodes de contagem/edição/sigla; listas manuais de rotas duplicadas; snapshots distintos sob uma data única; associação por filiação/identidade/biografia/palavra-chave; adoção automática de catálogo de 29 como universo exaustivo; preenchimento de lacunas; níveis de cobertura como mérito; ranking/score/afinidade; envio ou armazenamento de escolhas; publicação de dados privados ou brutos por copiar diretórios; release automático de branches ainda bloqueadas.

A publicação futura só é declarada conferida depois de teste real do endereço público. A aprovação técnica desta auditoria não encerra nenhuma issue editorial nem equivale a homologação de todas as candidaturas.

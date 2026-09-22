# GLOBAL-01 — gaps, lotes e handoff de execução

Referência: #40 -> #41 -> #42 -> #43 -> #44, sob o epic #39. Baselines e evidências em [current-editions.json](../data/global-integration/current-editions.json) e [evidence-index.json](../data/global-integration/evidence-index.json). As tasks abaixo são futuras; a GLOBAL-01 entrega diagnóstico e contrato proposto, sem aplicá-las à UI.

## Gaps por edição

| Edição | Preservar como contribuição | Adequar para integrar | Não promover automaticamente |
|---|---|---|---|
| SC/Federais | Leitura, macrogrupos, vínculo por trecho, coleção, compartilhar e retorno | Sair da raiz com ponte legada; adicionar shell; parametrizar edição/48 IDs/limites; partido realmente filtrável; novos campos de transparência por adapter | Matriz SC para outros nomes; 29 famílias como universo completo; ausência de tag como ausência de proposta |
| SC/Estaduais | Cadastro, origem do mandato, história contextual, informação não consolidada | Desacoplar render da raiz; rota com UF e alias; shell; evidência granular apenas quando disponível; coleção parametrizada | Mandato histórico como exercício atual; tema por profissão/biografia; pesquisa #4 como concluída |
| RS/Federais | Histórico de votos/status, natureza documental, fontes e revisões | Template independente do git show histórico; siglas derivadas de dados; filtro partidário explícito; shell; contrato de claims e coleção | Catálogo documental de 28 temas como apoio atual; escopo #34 como pesquisa feita; null como zero |
| RS/Estaduais | Research status separado da conclusão da rodada; ledger corretivo; melhoria de siglas | Reutilizar contrato de transparência sem publicar dados; template independente; shell/rotas/capabilities somente após gates próprios | Branch #9 como publicada; revisão parcial como integral; status de fonte bloqueada como falta de propostas |
| PR/Federais | Consulta combinada, mandato/história/localidade documentada, engine compartilhada e exports sanitizados | Desacoplar RS; imports de query singular/AND; schema de evidência por afirmação; catálogo revisado; shell/coleção | Região como base eleitoral; 25 temas como equivalentes automáticos a SC; usar as mesmas associações nos dois cargos |
| PR/Estaduais | Mesmas capacidades da engine PR, com dados próprios | Mesmo adapter técnico, mas validar separadamente IDs, fontes, contagens, temporalidade e flags | Paridade de código como paridade de pesquisa; junção das coleções federal/estadual |
| SP/Federais | Filtro multi-partido, parse/serialize, tema -> claims/fontes, controles recolhíveis e metadados de produto | Corrigir G04; compatibilizar URL/privacidade; distinguir semânticas; preservar extensão Ciência/Tecnologia; coleção testada em 249 registros | Atuação de 2026 como promessa atual; supor que Selecionados já existe; hub SP como evidência de edição estadual |

## Ordem por dependência e risco técnico

**Lote 0 — #41, fundação sem trocar a home:** congelar novamente o main efetivo, validar inventory, extrair templates/adapters e definir registry, identity, query, capability e DOM contracts. Preparar compatibilidade de links e testes de fronteira, sem redatar dados. Não alterar branches editoriais para caber no layout global.

**Lote 1 — #42, home/hubs/rota SC com compatibilidade:** usar registry e shell; introduzir home geral e hubs reais, mover SC preservando links antigos. Antes de ativar a raiz nova, testar rebuild das edições dependentes do molde antigo. A publicação da home não exige completar pesquisa nem ligar todo recurso da #43.

**Lote 2 — #43, componentes compartilhados e piloto:** generalizar Selecionados/fontes/retorno a partir de SC, validar contrato também com catálogo de 249 IDs e um catálogo sintético maior. Usar SC/Estaduais como primeiro adapter de transparência cadastral/histórica; isso testa uma estrutura diferente sem exigir filtros temáticos novos. Se faltar dado, capability fica bloqueada e a ficha permanece consultável.

**Lote 3 — #43, edições publicadas restantes:** PR/Federais e PR/Estaduais compartilham engine, mas têm relatórios/testes separados; SP recebe correção de âncora e separação semântica; RS/Federais recebe adapter histórico e navegação. A ordem interna pode ser ajustada por conflitos do main e capacidade técnica, nunca por importância política de candidaturas.

**Lote 4 — RS/Estaduais quando liberada:** consumir o contrato já testado, mas só publicar depois dos gates da issue #5/PR #9. Até lá, o hub informa apenas o estado permitido pelo catálogo, sem link para uma edição inexistente no Pages. Essa condição não bloqueia integração das seis edições publicadas.

**Lote 5 — #44, regressão e verificação pública:** validar o conjunto elegível para release, canonical/sitemap/aliases e rotas. Comparar dados/IDs/fontes antes/depois e conferir o endereço servido. Não somar testes de snapshots diferentes como um único total de homologação.

## Tasks obrigatórias para a #41

- [ ] **G2-A — catálogo:** schema + validator com publicação, pesquisa e capacidades independentes; ano/UF/cargo como contexto; não criar edição SP Estadual fictícia.
- [ ] **G2-B — desacoplamento:** documentar entradas ativas e extrair templates que hoje leem raiz, raiz histórica ou HTML RS pronto; teste de rebuild sem depender de outra edição publicada.
- [ ] **G2-C — roteamento:** resolver base path, rota SC com UF, alias estadual e ponte allowlisted para fragmentos antigos da raiz. Gerar fixtures de links legados reais antes de substituir a home.
- [ ] **G2-D — consulta:** modelo único de busca/partidos/status/mode; importadores PR e SP mantendo AND/OR e campos suportados; consulta em memória e compartilhamento explícito.
- [ ] **G2-E — semântica:** contratos separados de apoio atual e tema documentado; namespace de taxonomia, extensão SP preservada e conceitos pendentes de crosswalk. Nenhuma associação nova por inferência.
- [ ] **G2-F — ficha/transparência:** adapter de identificação, exercício de mandato, voto/histórico, claim/source e estado de pesquisa; campos desconhecidos continuam desconhecidos.
- [ ] **G2-G — coleção:** contrato parametrizado, remover dependência arquitetural de 48/SC, definir limites defensivos de importação sem truncamento silencioso; testar separação entre edições/anos.
- [ ] **G2-H — shell/metadados:** menus, breadcrumbs, home/hub data e sitemap derivados do mesmo registry; nenhuma lista de URLs duplicada em cada renderer.

**Gate para iniciar a troca pública da raiz na #42:** G2-A/B/C/H aprovados, e os demais contratos definidos a ponto de a home não cristalizar incompatibilidades. A implementação de todas as capacidades em todas as fichas fica na #43, não precisa ser antecipada artificialmente.

## Tasks de regressão que não podem desaparecer

- [ ] **G04-SP:** buscar `zzz-auditoria-sem-correspondencia-zzz`; alterar hash para ID de ficha existente; exigir ficha visível com aviso de eventual limpeza e possibilidade de retorno. Cobrir também entrada direta com query conflitante, popstate e ID desconhecido. O botão individual de SP já remove a query; não tratá-lo como a mesma reprodução.
- [ ] **SC-48:** arquivo compartilhado precisa iniciar com catálogos de 48, 97, 149 e 249, não somente SC. Validar ainda limites de importação e catálogo maior que 256.
- [ ] **SC-ROOT:** links antigos de candidato, fonte, partido e coleção preservam o alvo; raiz sem fragmento abre home; ausência de JS mantém rota de acesso.
- [ ] **SEMANTIC:** afirmação de atuação atual não se torna apoio atual; negativa/oposição mantém direção; sem data não ganha 2026; mudança de macrogrupo não cria associações.
- [ ] **DATA-PARITY:** ID, texto substantivo, fonte, snapshot, histórico/voto e notas corretivas protegidos; mudanças intencionais explicitadas por arquivo e versão.
- [ ] **SEO-ROUTES:** sitemap principal contém o conjunto de rotas realmente publicado/indexável, inclusive SC Estadual e PR; branch-only e aliases não viram duplicatas.
- [ ] **NOJS/A11Y:** leitura de cards/fontes sem JS, teclado, foco, painéis, retorno e ausência de obstrução em 320–1440; limites dos testes relatados.

## Limites e gestão das issues

#40 produz a base decisória. #41 implementa fundação; #42, home/hubs; #43, capacidades por lotes; #44, release. Não abrir sete novas issues que dupliquem pesquisa já existente. Issues editoriais (#1, #4, #5, #30 e demais aplicáveis) mantêm seus próprios critérios.

O único defeito funcional reprovado na bateria nova é G04; riscos de arquitetura e diferenças semânticas foram identificados por código/dados. A ação correta não é alterar os testes para excluir G04, mas preservá-lo como teste de aceitação de migração. O workflow observacional pode ser verde com finding registrado; a suíte de release não pode ocultar uma regressão assim.

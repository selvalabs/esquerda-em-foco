# ADR · fundação progressiva antes da home

Status: implementação de GLOBAL-02; liberação condicionada à validação da branch.

## Decisão

Não substituir os sete produtos por um template único. Introduzir catálogo,
contratos pequenos, adapters e shell independente. Manter os dados de cada edição
e aproveitar as contribuições confirmadas na GLOBAL-01. O ensaio usa as páginas
reais e rotas futuras, mas não toca o HTML público.

## Templates legados congelados

SC Estadual deixava o layout depender da raiz atual; RS Federal buscava a raiz
num commit histórico; PR e RS Estadual usavam o HTML pronto RS Federal. Congelar
os quatro inputs em `templates/global02/*.html.txt`, com ref/hash em manifest,
retira essas dependências do build. São inputs transitórios dos geradores legados,
não páginas navegáveis e não o novo sistema visual global. Os geradores continuam
substituindo cards por dados da própria edição; a suíte exige paridade das fichas.

A extensão `.txt` impede tratar os snapshots como edições públicas HTML. O conteúdo
é o legado público, não uma atualização de pesquisa. O custo de manter snapshots
redundantes é aceito temporariamente em troca de rebuild fiel. Extração de layout
sem conteúdo e consolidação completa dos renderers são migração posterior, não
motivo para reescrever pesquisas agora.

SC Estadual recebe um argumento explícito de baseline de isolamento. O padrão
histórico permanece; execuções novas podem fornecer hashes da versão efetiva sem
restaurar arquivos antigos para satisfazer um baseline ultrapassado.

RS Estadual continua no PR #9. O patch de desacoplamento é versionado no main e
testado num worktree descartável da ref auditada, com o pipeline incremental AD3,
sem push nessa branch, merge ou publicação. Uma atualização posterior da branch
exige reaplicação/revalidação, nunca substituir sua versão por este snapshot.

## Consequências

A #42 poderá trocar a raiz sem mudar os outputs desses geradores. A identidade
inclui ano para evitar coleções ou dados misturados em eleições futuras. Recursos
que precisam de pesquisa continuam bloqueados por dados, sem impedir a home.
O menu global usa links nativos e não depende de um framework novo ou backend.
Não há ranking, afinidade, coleta de preferências ou recomendação entre candidaturas.

## Gate de revisão

Conferir: schema; colisões de rotas; allowlist; coleções; importadores; adapters;
paridade e independência dos quatro pipelines; hash dos arquivos fora do escopo;
rehearsal em dois mounts; UI em sete larguras; fallback sem JavaScript.
Só então marcar #41 concluída. Build local sem navegador, workflow iniciado ou
artefato gerado não equivalem a todos esses gates aprovados.

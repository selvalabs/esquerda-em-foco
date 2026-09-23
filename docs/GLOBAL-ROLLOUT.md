# GLOBAL-04D4 · aplicação do padrão composto

Issue #56; baseline de entrada `51eb9195d836b984e73f05a845cf414ac1798e35`.
A conclusão/publicação deve ser registrada na issue/PR com o SHA efetivamente
verificado. A presença deste arquivo ou sucesso do gerador não declara release.

## Produto

Um painel progressivo de consulta nas seis edições usa os 39 temas e 16 grupos
reconciliados em D1. Partidos combinam por OU; dimensões combinam por E; temas e
grupos oferecem Qualquer/Todos, inclusive no Paraná. Grupo é união dos seus temas,
não atribuição a cada subtema. Contagens são de candidaturas distintas, sem ranking.

A ficha composta mantém a narrativa original, identificação, fontes e histórico,
com origem/limites e evidências expansíveis. O leitor de Selecionados movimenta o
mesmo artigo, não uma cópia ou uma síntese concorrente. Home/hubs e pesquisas não
são reconstruídos neste rollout. RS Estadual e a issue #50 permanecem fora.

## Evidência e mapeamento

`tools/global_rollout/projection.py` lê vínculos individuais existentes, fontes e
objetos reais. O crosswalk sozinho não cria associação; não há classificação por
palavra, partido, profissão ou biografia. Apoio atual, documentação temática e
contexto de síntese são recortes separados. O usuário pode abrir o objeto original,
sua fonte e o registro de origem para compreender cada resultado.

Os mapeamentos que exigiam revisão de objeto — seis registros de moradia RS e seis
de trabalho PR — estão explicitados em `config/rollout-object-decisions.json`, com
hash do texto, fonte e localizador. Uma mudança naquele texto invalida a decisão,
em vez de estender automaticamente a equivalência. Não se transformou atuação em
apoio atual nem se criaram medidas não mencionadas no registro.

Quando SP tem afirmação individual ligada a uma fonte mas não tem o localizador
interno do documento, o vínculo preserva seu recorte documentado e usa o ponteiro
**da afirmação no registro de pesquisa**, identificado como tal. A interface declara
que esse localizador não é trecho literal da fonte. O localizador externo ausente
continua ausente no painel de proveniência; não se inventa parágrafo, página ou
data. No legado RS/PR o ponteiro identifica a síntese/associação, não prova cada
frase separadamente. Isso preserva informação revisada sem fingir precisão maior.

SC Federal contém carreira em HTML. O adapter usa somente a indicação estruturada
de mandato acompanhada do texto e links de origem e a contagem de pleitos
explicitamente vinculada ao TSE. Não extrai votos de prosa nem transforma a flag
negativa em ausência de exercício. O filtro explica que preserva a indicação da
ficha anterior, não uma nova confirmação. Campos sem base estruturada suficiente
aparecem indisponíveis, com motivo — não preenchidos para obter paridade visual.

## Compatibilidade e privacidade

Novas consultas usam `eef=query&v=2`, com versão de taxonomia e edição. Os links v1
mantêm cláusulas nativas: não ampliar os macrogrupos antigos SC ou converter os
links PR de Todos para Qualquer. A interface identifica os critérios antigos. Um
novo filtro global é uma nova escolha explícita. Coleções v2 e SC v1 continuam
separadas por eleição/UF/cargo e não são alteradas pelo transporte de consultas.

Os estados de navegação ficam no documento; `history.state` contém somente chave
opaca. Compartilhar é ação explícita. Não há cookies, armazenamento persistente de
preferências, analytics ou envio de WhatsApp pelo controlador.

## Geração e manutenção

```bash
python tools/global_rollout/build.py
python tools/global03/publication.py --prepare
node --test tests/global_rollout/core.test.cjs
python tests/global_rollout/verify.py --baseline-root /tmp/eef-baseline --out /tmp/eef-qa/preservation.json
python tests/global_rollout/browser.py --out /tmp/eef-qa/browser
python tests/global_rollout/maintenance.py --out /tmp/eef-qa/maintenance
```

O decorador guarda posições dos nós originais, remove somente sua camada anterior
e lê novamente os JSONs atuais. Alterar metadados e regenerar uma ficha já composta
atualiza a proveniência — não existe atalho que reutiliza a marca antiga e deixa
informação desatualizada. O refresh de produção integra shell, seleção e a nova
consulta, sem deixar dois motores de visibilidade disputando as mesmas fichas.

`config/rollout-legacy.json` congela a sintaxe anterior, não preferências de usuários.
Associações e textos de consulta são sempre derivados dos dados atuais. Não executar
coletores históricos que gravam SC na raiz da home; o refresh recebe somente uma
saída editorial já revisada. Não copiar a galeria ou o diretório do protótipo D23.


## Ativação e histórico do contrato D1

Os campos `ui_active: false`, `status: specified_not_activated` em
`config/global-filter-taxonomy.json` e `activation: design_only` em
`data/global-integration/filter-capabilities.json` registram o **handoff histórico
da issue #53**. Eles não são reescritos retroativamente quando o rollout entra em
produção, porque servem de prova de que D1 definiu o contrato antes da ativação.

A fonte de verdade da ativação em produção é o conjunto
`config/editions.json` (capabilities por edição),
`data/global-rollout/status.json` e a seção `canonical_rollout` de
`data/global-integration/migration-status.json`. Isso separa especificação
histórica de estado operacional sem declarar que uma capability bloqueada por dados
ficou disponível apenas porque o componente existe.

## Testes e limites

As verificações novas comparam os textos, atributos, IDs e destinos das 760 fichas,
os dados e arquivos fora do escopo, a rastreabilidade dos vínculos e conjuntos
exatos de resultados por uma função de referência independente. O navegador testa
os seis produtos em dois mounts, sete larguras, contexto/evidência, consulta,
histórico, links antigos, Selecionados e funcionamento sem JavaScript.

Os testes D1/D23 que exigem o HTML histórico intacto pertencem ao snapshot de sua
etapa; não são reexecutados contra um HTML que esta issue deliberadamente altera.
O snapshot é conferido separadamente. A preservação do conteúdo e os contratos
ativos são verificados pelas suítes de rollout, sem enfraquecer as comparações.

Não há nova coleta eleitoral, verificação externa atual de mandato ou posição,
mensagem real enviada, teste em aparelho físico ou certificação integral de
acessibilidade. Hash de fonte valida rastreabilidade, não veracidade política.

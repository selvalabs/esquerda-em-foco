# Taxonomia v1 — contrato editorial e técnico

Issue #20, Round 1. Recorte documental de 21/09/2026. A interface de filtros NÃO é ativada neste round.

## Fonte canônica

- `config/topics-v1.json`: versão 1.0.0, IDs estáveis, nomes, inclusão, exclusão e aliases.
- `data/sc-federais-topics-v1/decisions.json`: decisões humanas por afirmação, objeto, direção e fonte.
- `data/sc-federais-topics-v1/matrix.json`: 48 registros, inclusive os vazios; associações e fontes resolvíveis.
- `data/sc-federais-pautas/review.json`: revisão editorial de origem; histórico, limitações e percursos de pesquisa.
- `data/sc-federais-topics-v1/provenance.json`: commit da pesquisa e base de integração.
- `data/sc-federais-topics-v1/integration-qa.json`: teste da integração atual. O `qa.json` em `sc-federais-pautas` documenta o round anterior, não este.

As 29 famílias preliminares foram mantidas, com regras explícitas. Saúde pública e SUS passou a **Saúde**: uma menção genérica não sustenta uma posição específica sobre SUS. Apostas e proteção econômica passou a **Apostas e jogos de azar**, para não presumir sentido de posição pelo nome da categoria.

Categorias sem correspondência elegível continuam no catálogo compartilhado; isso não obriga a mostrá-las como botões ativos. As contagens medem documentação, não mérito político.

## Duas perguntas diferentes

**Existe uma posição documentada sobre este assunto?** Usar `eligible_current_position`. Esse conjunto pode conter apoio, prioridade, oposição, debate ou atuação, sempre com direção e objeto visíveis.

**Há apoio ou prioridade explicitamente documentados para este objeto?** Usar `eligible_current_support`. É o conjunto conservador preparado para o pedido de filtros de pautas defendidas. Não inclui apenas oposição, requerimento de debate ou ato de participação registrado sem declaração de apoio.

Em nenhum caso é correto exibir automaticamente `apoia + nome da família`. A relação é com o `position_target`, não com todas as políticas que cabem no assunto. Por exemplo, Saúde não implica apoio à cannabis; Educação não implica uma posição sobre ensino domiciliar; oposição às bets não é apoio às apostas.

O Round 2 deve usar os IDs/conjuntos aprovados, sem classificar os textos novamente por palavras-chave. Um eventual filtro neutro por assunto precisa ser rotulado como tal e mostrar o sentido da posição; não pode substituir silenciosamente o filtro de apoio.

## Temporalidade e autoria

Evidência de 2026 pode decorrer de data original ou de contexto eleitoral identificado na revisão. Data de consulta não data o conteúdo. Uma fonte sem data original, mas explicitamente situada na campanha de 2026, é diferente de uma apresentação cujo período é desconhecido.

Registros exclusivamente históricos, apresentações sem período determinado e atribuições conjuntas por outro participante não alimentam os filtros de posições atuais. Continuam disponíveis na matriz, no texto dos cards e em Fontes e contexto. As limitações não são apagadas.

A própria candidatura coletiva identificada no registro não é confundida com atribuição de terceiros: a publicação autoral da coletiva e um material de outro candidato recebem tratamentos diferentes.

As elegibilidades valem para o recorte documental de 21/09/2026, não constituem verificação contínua. Novas declarações podem exigir revisão posterior.

## Matriz

Cada associação contém:

`association_id → candidate_id → topic_id → claim_id → direction → position_target → period → source_ids`

As fontes são resolvidas pelo registro `sources`, com URL, editor, tipo, data quando confirmada, período, localizador e proveniência. Em grupos de frases com fontes diferentes, a associação aponta somente para a fonte pertinente. A construção do PNE, o orçamento participativo e a oposição às bets, por exemplo, não devem compartilhar referências indiscriminadamente.

Os 48 registros estão presentes mesmo quando não há nenhuma associação. Lista vazia significa lacuna documental, nunca oposição, ausência de propostas ou juízo de qualidade. O Round 2 precisa informar essa limitação ao filtrar.

## Regras da futura interface

O universo sem filtros mantém as 48 fichas. Busca e filtros operam em conjunto. OR é o padrão; AND poderá ser oferecido como “Todas as selecionadas”. A rotação diária permanece responsável pela ordem; quantidade de temas não altera posição nem produz relevância, score ou recomendação.

Categorias terão mesma apresentação e ordem alfabética. Informar se as contagens são totais do recorte ou condicionadas à busca; testar ambos os casos conforme a opção implementada. Mostrar filtros ativos, limpar e estado sem resultados. Links individuais devem continuar localizando a ficha, inclusive quando um filtro precisar ser removido para revelá-la.

Desktop: filtros abaixo dos partidos, com área acessível caso a sidebar seja mais alta que a tela. Mobile: botão próximo da busca e painel com foco, teclado e fechamento corretos. Não duplicar IDs ou manter dois estados de seleção divergentes.

## Replicação e versões

Outras frentes podem importar o catálogo e o contrato. Não podem copiar a associação de um partido ou pessoa para outra. IDs de candidatura, fontes, direção e temporalidade são específicos do levantamento. Este round não altera RS, SP, PR nem SC estaduais.

IDs nunca são reciclados. Novos temas compatíveis elevam a versão minor; mudança de sentido ou remoção exige versão major e migração explícita. Aliases auxiliam a documentação, não autorizam classificação automática.

## Reprodução

Na raiz, em Python 3.12 com BeautifulSoup e Playwright:

```sh
python tools/sc_federal_taxonomy/prepare.py
python tools/sc_federal_taxonomy/build.py
python tools/sc_federal_taxonomy/qa.py
```

`prepare.py` importa arquivos da pesquisa pinada apenas quando ausentes e reaplica somente blocos de pautas ao index atual. Nunca copia o index antigo. O arquivo de baseline da pesquisa permanece imutável. O QA compara a integração com o main usado na execução, não confunde mudanças concorrentes legítimas com alterações deste round e testa reconstrução idempotente.

No workflow de pull request, `PRESERVATION_BASE` é a base do PR; por execução local, pode ser fornecido um commit para a comparação. O script falha se detectar alteração de conteúdo fora dos blocos autorizados ou de arquivos protegidos.

## Gates

Round 1: pesquisa integrada e publicação conferida, taxonomia e matriz versionadas, QA da base reconciliada. A issue #6 só será encerrada depois dessa conferência. A issue #20 permanece aberta para o Round 2.

Round 2: interface, transparência pública dos filtros, testes combinatórios, regressão e publicação. Nenhum código visual de filtro foi incluído no Round 1.

# RS / Deputados estaduais — execução A–D

**Corte editorial:** 21/09/2026. **Branch:** `feat/rs-deputados-estaduais`. **Issue:** #5. **PR:** #9.

**Entrega incremental, sem merge ou publicação.** A–D receberam pesquisa, implementação e atualizações de dados. A pesquisa não foi encerrada para todas as candidaturas; E e F continuam reservados à revisão final.

## Comparativo verificável

| Cobertura | Antes | Depois | Variação |
|---|---:|---:|---:|
| Candidaturas no recorte | 145 | 149 | +4 |
| Sínteses de pautas ou temas com fonte | 30 | 50 | +20 |
| Candidaturas ainda sem síntese | 115 | 99 | -16 |
| Mandatos atuais confirmados | 5 | 15 | +10 |
| Fichas com atos ou registros institucionais | 15 | 26 | +11 |
| Registros históricos com votos conferidos | 326 | 392 | +66 |

As linhas medem cobertura documental, não avaliam candidaturas. Uma mesma pessoa pode estar em vários grupos. Síntese de temas, confirmação de cargo e registro de um ato são verificações diferentes.

## A — Pautas individuais

Foram acrescentadas 20 sínteses às 30 existentes. As adições usam páginas individuais, programas legíveis, entrevistas e registros institucionais identificados. Restam 99 candidaturas sem síntese temática. Não se afirma busca exaustiva de todas elas. A situação de cada ficha e os próximos passos estão em `candidate-coverage.csv` e `.json`.

O programa de Humberto Matos foi recuperado no HTML, sem atribuir a ele respostas de formulário. A página de propostas de Vinicius Bondan foi ligada ao site individual, para evitar atribuição por domínio genérico. Materiais que ainda se apresentam como pré-campanha não substituem a situação de registro do TSE. Relatos de atuação anterior e prioridades gerais não foram apresentados como programas completos.

## B — Mandatos atuais

Foram acrescentadas 10 confirmações a partir de diretórios institucionais de Santa Maria, Passo Fundo e Caxias do Sul. O total confirmado nesta base é 15. Resultados eleitorais antigos, autodescrição de campanha e uma notícia pontual não foram convertidos em confirmação de exercício atual.

O diretório da ALRS continuou sem leitura utilizável nas tentativas registradas. Também houve bloqueios de acesso em diretórios municipais. Essas limitações estão em `data/rs-estaduais/phase2-source-review.json`. Não confirmar um cargo significa informação desconhecida nesta edição, não inexistência de mandato.

## C — Atuação institucional

A cobertura passou de 15 para 26 fichas com atos ou registros institucionais. As adições incluem proposições, relatorias, composição de comissões, reuniões de frentes, pronunciamentos e pedidos de informação. Cada adição tem fonte e data; notícia de gabinete é identificada como tal.

Quando a notícia não informou o dia do ato, registrou-se explicitamente a data da publicação, com `event_date: null`. Quando não informou número da proposição, o campo permanece nulo e a conferência do processo continua pendente. Aprovação legislativa não foi chamada de sanção; pedidos e denúncias não foram tratados como resultados ou irregularidades comprovadas.

## D — Históricos e votos

A recuperação de fontes de 2004, 2006, 2008 e 2010 acrescentou 66 registros nominais conferidos, totalizando 392 de 432 linhas históricas. Em 2004, identificadores repetidos entre municípios exigiram incluir unidade eleitoral, cargo, turno, ano, número e nome civil no cruzamento. As quatro fontes antigas passaram pela validação contextual; cópias de auditoria preservam os resultados anteriores à revalidação.

| Situação histórica | Registros |
|---|---:|
| Votação nominal conferida | 392 |
| Sem correspondência segura na fonte | 13 |
| Vice: votação nominal própria não se aplica | 24 |
| Disputa fora da população RS coletada | 1 |
| Suplência: votação nominal própria não se aplica | 2 |

Cada linha ainda sem votação aparece em `historical-vote-pendencies.csv`, separando ausência de correspondência, população não coberta e situações não aplicáveis. Nenhum nulo foi convertido em zero. O hash nacional do ZIP permanece nulo para acesso por intervalos; o membro RS completo possui CRC e SHA-256 próprios.

## Regressão e preservação

Testes unitários: **46**. Verificações Chromium: **47**. Resultado combinado: **passed**. O workflow verifica o isolamento das frentes existentes. Esses testes são regressões do incremento A–D, não declaração de encerramento da revisão editorial independente E/F.

O cadastro eleitoral conserva o snapshot **21/09/2026 12:31:37**. Não houve nova coleta eleitoral nesta fase nem alteração de data para simular atualização. A nova reconciliação TSE/DivulgaCand continua na etapa F.

## Continuidade

Prosseguir com as 99 sínteses pendentes, ampliar confirmação institucional de mandatos e conferir processos/atos sem identificador completo. Revisar as linhas nominais ainda sem correspondência ou fora do recorte, sem incluir vice/suplência nessa conta. Em seguida, executar E e F sobre a versão consolidada. A issue #5 e o PR #9 permanecem abertos; não houve merge ou publicação.

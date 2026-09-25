# RS-EST-AD3 — incremento substantivo, execução parcial

**Dados e interface validados; pesquisa integral das 88 fichas não concluída.**

Baseline: `b9ec0c352cdc0dc2a77be8ea4cf28469f1c09502`. Código validado: `ad2faed0d303fc8cda12987d28b16359624719ec`.

## Conteúdo incorporado

11 novas sínteses, 3 confirmações institucionais e 3 atos datados. Uma listagem com vínculo individual insuficiente foi retirada da contagem e preservada como revisão documental.

| Indicador | Antes | Depois |
|---|---:|---:|
| Candidaturas | 149 | 149 |
| Sínteses | 61 | 72 |
| Sem síntese | 88 | 77 |
| Mandatos confirmados nas fontes datadas | 16 | 19 |
| Fichas com atos | 31 | 31 |
| Atos individuais documentados | 44 | 46 |
| Linhas históricas | 432 | 432 |
| Votos conferidos | 395 | 395 |

## Cobertura da investigação

A fila contém 88 identidades. 88 receberam consultas ou leituras registradas; 11 obtiveram evidência suficiente para novas sínteses. Os outros 77 casos têm investigação parcial. Não se confunde consulta nominal, disponibilidade HTTP ou simples classificação com pesquisa completa.

Foram registrados 128 termos de busca efetivamente executados. Páginas sem conteúdo, homônimos, bloqueios e modelos provisórios não viraram pautas.

## Mandatos e revisão de atribuição

Braite, Amaral Negrito e Danrlei Massena foram confirmados em diretórios da legislatura atual 2025–2028 como ativos e titulares, com perfis e nomes civis conciliados. As confirmações anteriores não foram redatadas.

O registro SISTCOP 331235 aparece sob blogs de vereadores diferentes e não indica autoria. Um PDF de ementa semelhante possui protocolo 30650, de 23/12/2020, e outra assinatura. Esse protocolo não foi atribuído a Bruno Berté. O vínculo individual continua não confirmado; a listagem foi retirada da contagem, sem afirmar inexistência de atuação da pessoa no tema.

## Histórico e limites

Onze fichas históricas foram relidas, mas não forneceram totais novos. Permanecem onze totais sem correspondência segura e 26 posições de vice/suplência sem voto próprio. Nenhum indeferimento ou renúncia virou zero. A investigação nominal desses casos ainda precisa avançar além do cadastro.

## Validação

Testes atuais AD3: 41, sem skips. Controles de navegador atuais: 63. Os 92 testes e 63 controles da recuperação anterior foram executados separadamente no commit congelado, sem enfraquecer invariantes ou aplicá-las indevidamente a contagens novas.

A integração é incremental e reproduzível. Foram preservados IDs, recorte, votos validados e datas eleitorais. Antes da integração incremental, o workflow antigo havia atualizado metadados e consultas de disponibilidade em cinco relatórios de recuperação. Essas mudanças preexistentes foram identificadas, mantiveram as métricas substantivas e o HTML anterior, e foram preservadas como recebidas. As evidências e as duas referências de isolamento estão em `isolation.json`; a comparação das demais frentes continua no baseline original.

## GitHub e próxima etapa

Mesma issue #5, PR #9 e branch. Sem merge, deploy ou alteração de outras frentes. Snapshot eleitoral: 21/09/2026 12:31:37. Pesquisa nova: 22/09/2026. Aprofundamento das lacunas, auditoria E e coleta/delta F permanecem pendentes.

Evidências em `data/rs-estaduais/ad3/` e `docs/rs-estaduais/ad3/`: cobertura individual, lotes, nulos históricos, testes e relatório quantitativo.

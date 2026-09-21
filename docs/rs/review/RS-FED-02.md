# RS-FED-02 — revisão editorial e factual

Execução autorizada pelo usuário em 21/09/2026. Continuidade da issue #1.

## Referência e isolamento

Baseline publicado: `810a7896b3355254d50852761a41bae31ce3f567`.
Branch de trabalho: `feat/rs-federais-revisao-editorial`.
A rodada reutiliza as coletas e auditorias já existentes nesta branch. Não reinicia nem sobrescreve o trabalho anterior.

Alterações permitidas: `data/rs/`, `docs/rs/`, `tools/rs/`, `tests/rs/`, `rs/deputados-federais/` e workflow exclusivo desta rodada. Demais páginas, assets compartilhados e frentes estaduais devem permanecer intactos. Conferir novamente o main antes da integração para preservar alterações concorrentes.

## Trabalho

1. Revisar as 107 fichas do recorte, as 28 sínteses existentes e as 79 lacunas originais. Registrar consultas e fontes por ID eleitoral estável.
2. Publicar apenas informações individualmente sustentadas, separando trajetória, proposta, atividade legislativa e execução. Declarações de campanha e biografias de gabinete devem ser atribuídas.
3. Verificar cargos atuais em diretórios e registros institucionais, distinguindo eleição, posse, suplência, licença e exercício. Ausência de confirmação não prova ausência de cargo.
4. Reconciliar históricos e votos por identidade, cargo, local, ano e turno; diferenciar zero, dado não conferido, pleito não realizado e voto nominal não aplicável.
5. Auditar os endereços declarados; rejeitar credenciais embutidas, domínios malformados e esquemas inseguros. Corrigir somente com confirmação, preservando o original como proveniência. Bloqueio de acesso não equivale a link inexistente.
6. Organizar temas com evidência específica por candidatura. Menção isolada não equivale a apoio; nenhuma pauta é herdada automaticamente do partido. Não adicionar novos filtros visuais nesta rodada.
7. Registrar nova consulta eleitoral e divergências antes de publicar. A base continua sendo um retrato datado, sem atualização recorrente instalada.
8. Executar revisão editorial, validações de fontes e dados, testes funcionais, responsividade e regressão. Preservar a URL e as âncoras individuais.
9. Integrar por PR somente após os testes e verificar os arquivos realmente servidos pelo GitHub Pages.

## Registros de pesquisa

Cada candidatura terá identificação, consultas realmente realizadas, fontes e sua natureza, período dos fatos, campos documentados e lacunas. Biografia documentada, pauta documentada, cargo confirmado e revisão realizada são métricas separadas. Um aviso de informação insuficiente não conta como síntese preenchida.

## Gates

- Nenhuma afirmação nova sem fonte pertinente.
- Nenhum ranking, recomendação eleitoral, prognóstico ou linguagem promocional.
- Nenhum registro histórico convertido automaticamente em candidatura ou cargo atual.
- Nenhum voto ausente convertido em zero; votos de chapa não atribuídos nominalmente a vice.
- Nenhum canal inferido por semelhança de nomes.
- Nenhum dado pessoal privado acrescentado ao conteúdo publicado.
- Nenhuma alteração em SC ou nas demais frentes durante esta integração.
- Testes e verificação pública registrados, com resultado real.

## Conclusão e limitações

A meta é executar o roteiro em todas as fichas e melhorar a cobertura documental. A documentação pode continuar insuficiente para determinados campos. Registrar essas lacunas explicitamente e não contabilizá-las como conteúdo completo. Manter a issue aberta enquanto seus critérios editoriais originais não estiverem atendidos.

Entregáveis: dados e página atualizados, controle da pesquisa, relatório antes/depois, procedimento manual reproduzível, testes, PR/commit e verificação da publicação. Automação recorrente, redesign, filtros novos e novas frentes ficam fora desta rodada.

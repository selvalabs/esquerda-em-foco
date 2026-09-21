# RS-FED-02 — reprodução e atualização manual

## O que é automático e o que não é

A rotação diária altera somente a exposição visual. Não consulta o TSE, não pesquisa propostas e não atualiza mandatos. Esta edição registra uma consulta de 21/09/2026. Não há tarefa recorrente instalada.

O build é offline: combina fontes previamente coletadas e decisões editoriais versionadas. Nenhum tema é atribuído por partido, profissão ou ocorrência isolada de palavra.

## Reproduzir a edição revisada

Usar um clone completo do repositório, com os commits `71d123b909cdbf3d84bd1cdca89511890759d395` (referência visual) e `810a7896b3355254d50852761a41bae31ce3f567` (publicação preservada). Eles são referências diferentes; não restaurar o HTML antigo sobre SC.

Ambiente usado na validação: Python 3.12; beautifulsoup4 4.13.4; lxml 6.0.2; Pillow 11.3.0; Playwright 1.55.0 e Chromium.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install beautifulsoup4==4.13.4 lxml==6.0.2 Pillow==11.3.0 playwright==1.55.0
python -m playwright install chromium
$env:EEFOCO_OFFLINE_BUILD = '1'
python tools/rs/upgrade_review.py
python tools/rs/build.py
python -m unittest discover -s tests/rs -p 'test_*.py' -v
python tools/rs/qa.py
```

`upgrade_review.py` instala migrações idempotentes, preserva o JavaScript publicado, prepara os insumos editoriais congelados e gera o controle da pesquisa. O renderer escreve apenas os arquivos próprios do RS. Não foram implantados novos controles de filtros.

## Nova rodada de pesquisa

Criar uma branch a partir do main mais recente e registrar o commit de referência. Não reaproveitar automaticamente a antiga baseline para comparar arquivos de outras frentes que tenham evoluído desde então.

1. Guardar os relatórios e hashes da rodada anterior em uma pasta histórica. Preservar a origem das informações em vez de apagar evidências anteriores.
2. Executar explicitamente `python tools/rs/review_collect.py` para nova consulta oficial. Examinar `docs/rs/review/official-refresh.json`. Se houver erros, perfis não atualizados, IDs acrescentados ou removidos, interromper a publicação e reconciliar o universo antes de continuar. Um comando concluído sem exceção não garante que o relatório esteja sem erros.
3. Revisar separadamente novas situações eleitorais, substituições e fontes institucionais de cargos. Resultado de eleição ou entrada em um diretório histórico não comprova exercício atual.
4. Conferir o histórico e os votos por identidade, cargo, local, ano e turno. `review_votes.py` preserva um marcador para não repetir downloads; uma nova coleta exige arquivar o relatório anterior e remover somente esse marcador de controle. Nunca converter ausência de valor em zero nem atribuir votos de chapa ao vice.
5. Registrar a redação e suas referências em `data/rs/review-editorial.json` e `data/rs/review-addendum.json`. Os novos registros são aplicados em ordem sobre `editorial-baseline.json`; não editar apenas o HTML nem apenas o arquivo editorial gerado. Cada tema deve apontar para a fonte individual que o sustenta. Fatos históricos devem manter seu período.
6. Registrar as consultas efetivamente feitas em `review-searches.json`. O controle gerado diferencia busca, disponibilidade HTTP, fonte editorial e confirmação institucional. Não acrescentar buscas que não foram realizadas.
7. Para canais inválidos, só adicionar uma substituição depois de confirmar a vinculação à candidatura. Nome de usuário sem plataforma não autoriza inventar um Instagram. Erro 403 ou exigência de login não prova que o site foi removido.
8. Atualizar as datas efetivas de coleta e revisão nos scripts/metadados/textos pertinentes; não trocar datas apenas para aparentar atualização. Mudanças no universo exigem revisar os testes que fixam o snapshot de 107 registros e os relatórios de cobertura.
9. Reproduzir o build, executar todos os testes e comparar dois builds sucessivos. Alterações não determinísticas precisam ser resolvidas antes da integração.
10. Conferir novamente o main, integrar por PR e verificar o conteúdo servido no Pages contra os hashes do commit. Preservar as demais frentes e o sitemap existente.

## Relatórios

- `final-report.json`: cobertura editorial, biográfica, de mandatos e de votações, separadas.
- `candidate-matrix.json`: campos documentados e lacunas por identificação eleitoral.
- `data/rs/review-search-log.json`: consultas e fontes por ficha; não é uma certificação de completude.
- `declared-links-review.json`: disposição de todos os endereços rejeitados, sem reproduzir contatos indevidamente como canais.
- `source-http-review.json`: disponibilidade técnica, não validação semântica de todas as páginas.
- `unit-tests.txt` e `docs/rs/browser-qa.json`: resultados efetivos dos testes.

Uma biografia não substitui uma síntese de propostas. Uma ficha com pesquisa realizada e documentação insuficiente continua parcial. A issue editorial deve permanecer aberta enquanto seus critérios não estiverem atendidos.

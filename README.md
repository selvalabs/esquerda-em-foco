# Esquerda em foco

Caderno de consulta de candidaturas, trajetórias e documentação individual com fontes. A cobertura é parcial e datada; não há ranking, pontuação, afinidade ou recomendação de candidaturas.

## Organização

A entrada geral apresenta quatro estados. Cada hub direciona aos cargos publicados:

- Santa Catarina: deputados federais e estaduais.
- Rio Grande do Sul: deputados federais; estaduais em preparação, sem publicação.
- Paraná: deputados federais e estaduais.
- São Paulo: deputados federais.

O catálogo `config/editions.json` separa publicação, pesquisa e disponibilidade de recursos. Dados, fontes e snapshots permanecem próprios de cada edição. O recorte de partidos é explícito em `config/party-scope-2026.json`.

## Site estático

Destino de produção: https://selvalabs.github.io/esquerda-em-foco/

A home está na raiz, hubs em `/{uf}/` e edições em `/{uf}/deputados-federais/` ou `/{uf}/deputados-estaduais/`. A compatibilidade preserva fragmentos antigos de SC na raiz e mantém alias para `/deputados-estaduais/`. A integração funcional GLOBAL-04 foi reconciliada no PR #61. A revisão final GLOBAL-05 permanece na issue #44; existência de arquivos ou merge não substitui verificação do deploy.

## Desenvolvimento e preservação

Documentação da interface e manutenção: `docs/GLOBAL-03-HOME.md`.
Decisões por composição: `docs/GLOBAL-CANONICAL-DECISIONS.md`.
Contratos da fundação: `docs/GLOBAL-EDITIONS-CONTRACT.md` e `docs/GLOBAL-02-CONTRACTS.md`.

Os renderers legados precisam da etapa `tools/global03/refresh.py` após gerar páginas, para reaplicar rotas e navegação sem alterar a pesquisa. Não executar o bootstrap GLOBAL-02 contra a nova raiz; ele é uma referência histórica. Não copiar associações de temas entre pessoas/edições, converter nulos em zero ou atualizar snapshots implicitamente.

A validação usa baselines explícitos, testes de lógica, checks de integridade e navegador. Os workflows de GLOBAL-03 distinguem compilação, QA e conferência pública por HTTP/SHA-256. Fontes externas bloqueadas, lacunas documentais e testes não realizados permanecem limitações, não evidência de conclusão.

## Consulta global e fichas

As seis edições publicadas compartilham o painel de 39 temas em 16 grupos,
multisseleção partidária, Qualquer/Todos e consulta compartilhada v2, com
compatibilidade anterior. Tema documentado, apoio atual e contexto herdado não
são equivalentes; a cobertura de pesquisa continua diferente entre as edições.

A ficha composta preserva a narrativa e acrescenta acesso a mandato/histórico,
fontes, datas e limites. Selecionados utiliza o artigo original, por eleição,
UF e cargo; não há caderno persistente multi-edição neste escopo (#50).

Fontes operacionais: `config/editions.json`, `data/global-rollout/status.json` e
`data/global-integration/reconciliation.json`. Documentação: `GLOBAL-ROLLOUT.md`,
`GLOBAL-CARD-HANDOFF.md` e `GLOBAL-04-RECONCILIATION.md`, em `docs/`.

## GLOBAL-05: candidato de correção e QA

O patch da #44 corrige abertura do menu SP, âncoras dentro de Selecionados,
recuperação de foco ao remover filtros e metadados de compartilhamento SP.
**O pacote local não é uma publicação nem encerra a #44.** Resultados e limites:
`docs/GLOBAL-INTEGRATION-QA.md` e `docs/GLOBAL-INTEGRATION-PUBLICACAO.md`.

Após uma geração editorial autorizada, executar o refresh apropriado e
`python tools/global03/publication.py --prepare`. A preparação também reaplica
metadados ausentes e revisões de CSS/JS por conteúdo antes de atualizar o manifesto.
Não atualizar datas da pesquisa como efeito colateral dessa preparação.

# SC Federais — Round 1 concluído e publicação conferida

Data: **21/09/2026**. PR **#24**. Continuidade da revisão **#6** e do plano em dois rounds da **#20**.

## Estado final

A revisão de pautas, a taxonomia documental v1 e a matriz de evidências foram integradas ao `main` e a publicação foi conferida por HTTP e SHA-256. **Nenhum filtro visual foi implementado ou ativado neste round.**

- PR: https://github.com/selvalabs/esquerda-em-foco/pull/24
- Commit integrado: `0f2ab52ef07b0f9ae0f7c992b3120962c40fc7f6`.
- Main imediatamente anterior: `cb0617c6728739e5a0b85ff30398c67d138b0301`.
- Fonte da pesquisa reaplicada: `c2ce0d44f64c72c5949d373fa210d9144948d310`.
- Site: https://selvalabs.github.io/esquerda-em-foco/

O HTML antigo não foi copiado. As alterações de pautas, contexto e metodologia foram reaplicadas ao index atual. A integração preservou as mudanças concorrentes de SC estaduais e os arquivos preexistentes das demais frentes.

## Entregas visíveis no site

As 48 fichas mantêm seus dados eleitorais, imagens, âncoras e ordenação diária. Foram integradas as sínteses revisadas e o bloco **Fontes e contexto** de cada ficha, com referências, período e limitações. A explicação metodológica diferencia material eleitoral, manifestação pública, histórico, apresentação sem período determinado e atribuição conjunta.

Navbar, menu hambúrguer, busca, rodapé e configuração de métricas desativadas não foram redesenhados ou substituídos.

## Cobertura documental

- **48** registros individuais na matriz, inclusive os sem associações.
- **29** fichas com alguma pauta documentada em algum período.
- **19** fichas com documentação acessível insuficiente, sem associações inventadas.
- **29** famílias temáticas no catálogo compartilhado v1.0.0.
- **156** associações revisadas, relacionadas a **52** grupos de afirmações e **36** registros de fontes.
- **21** fichas com posição individual situada em 2026: **131** associações elegíveis para consulta neutra por assunto.
- **20** fichas com ao menos um apoio ou prioridade explicitamente documentados em 2026: **123** associações elegíveis para esse recorte mais restrito.

Esses conjuntos não medem mérito político. A diferença entre posição e apoio decorre da distinção entre apoio, prioridade, oposição, debate e atuação documentada. Material exclusivamente histórico, sem período determinado ou com atribuição conjunta pendente permanece registrado, mas não recebe elegibilidade automática para filtros atuais.

A etapa fecha um protocolo de revisão datado, não afirma que a documentação programática de todas as candidaturas esteja completa. Tampouco é um novo censo ou atualização de registros eleitorais.

## Taxonomia e rastreabilidade

`config/topics-v1.json` contém IDs estáveis, rótulos, inclusão, exclusão e aliases. **Saúde** não significa automaticamente apoio específico ao SUS ou a qualquer outra medida. **Apostas e jogos de azar** conserva o sentido de cada posição; oposição não é convertida em apoio à atividade.

`data/sc-federais-topics-v1/matrix.json` conserva:

`candidate_id → topic_id → claim_id → direction → position_target → period → source_ids`

As decisões estão em `data/sc-federais-topics-v1/decisions.json`. Cada associação aponta apenas para as fontes pertinentes ao objeto indicado. Nenhuma classificação foi gerada por palavras-chave, legenda, profissão, identidade ou nome de urna.

O atributo antigo `data-has-pauta` no HTML não é sinal de elegibilidade atual: também pode corresponder a síntese histórica. O Round 2 deverá consumir a matriz e seus campos de elegibilidade.

## Validação antes da integração

### Preparação

Run: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35642442416

**296 verificações aprovadas, zero falhas**. A primeira base `38e66f643048a00f15a70d6f7be3a69e83cf4c23` teve seus 685 arquivos preexistentes, exceto o index autorizado, preservados byte a byte.

### Merge candidato sobre o main atualizado

Run: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35642819211

Job `pr-validation`: **106475992452**, concluído com sucesso.

- Base efetiva: `cb0617c6728739e5a0b85ff30398c67d138b0301`.
- Merge candidato testado: `cd25c59d6890f15992af8ffa8df7ce8aed5b2102`.
- **296 verificações aprovadas, zero falhas**, incluindo preservação dos arquivos da base efetiva, não apenas do snapshot anterior.
- Árvore do merge candidato e da integração final: `dba935205e8d5a1ba1e9f7c889582b02d1595515`.

Testes Chromium em **320, 360, 390, 430, 768, 1024 e 1440 px**: busca, limpar busca, ausência de resultado, fontes/contexto, navbar sticky, menu mobile e Escape, links internos, rotação dos partidos e das candidaturas, IDs únicos, ausência de overflow e de erros JavaScript. A reconstrução dos arquivos é idempotente.

Imagens externas foram bloqueadas nesses testes. Capturas estão no artifact do run; não se afirma teste em aparelho físico nem revisão visual de todas as imagens externas.

O relatório em `data/sc-federais-topics-v1/integration-qa.json` registra a primeira preparação. A execução sobre a base atualizada está no log e artifact do run do PR acima; o `qa.json` da pasta de pesquisa permanece como proveniência do round anterior.

## Fontes

A verificação de disponibilidade abrangeu **36 URLs/registros**, sem respostas 404/410 pendentes. Leituras anteriores de redes sociais mantêm seus registros e não foram repetidas automaticamente. Resposta HTTP não comprova autoria ou conteúdo, e bloqueio não equivale a inexistência de propostas.

Uma reconferência editorial pontual de quatro fontes, especificamente para direção e temporalidade, está registrada em `data/sc-federais-topics-v1/source-spot-check.json`. Não foi apresentada como nova pesquisa integral das 48 pessoas.

## Publicação efetivamente conferida

Run: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35643093167

Job `verify-published`: **106476908658**, concluído com sucesso.

Conferência em **2026-09-21T19:10:24.821409Z**, equivalente a 16:10:24 no horário de Brasília. **7/7 arquivos responderam HTTP 200 e coincidiram em SHA-256 com o commit integrado.**

| Arquivo | SHA-256 publicado e esperado |
|---|---|
| `index.html` | `8a9bdffb2ad20a53857c0ac3fd4d02ce9980e10dd162235479971f4e63ffe2f5` |
| `assets/sc-federais-pautas.css` | `561e6aef71d716f1ff4c74214697c476d5182c1f53da46305d832772ac858fd8` |
| `config/topics-v1.json` | `c042916a25c2e8a25eea0b735421630e13385183e4d66e56510e2680c8bfdaf4` |
| `data/sc-federais-pautas/review.json` | `63c82e77928937230f63c3d5f0ce8b96d516447487522e690c2a021859d9bf6b` |
| `data/sc-federais-topics-v1/matrix.json` | `6c6153a081bbdda250ebff97b23798e8c896c1e999461a44968f5b913e1a55fb` |
| `data/sc-federais-topics-v1/coverage.json` | `97a5109ae39ded3b638fbbdf0685c8791bae52e7b5377eb59e047927a7813885` |
| `docs/TOPICS-V1-CONTRACT.md` | `d174f63f6b7bf5fd381fd419bd3e0b40918cc877b7edf7d5716a73e4236e82e7` |

## Continuidade

O escopo de revisão e publicação da **#6 está entregue**, com as 19 lacunas explicitadas. O **Round 1 da #20 está concluído**. A #20 continua para o **Round 2**, que implementará filtros desktop/mobile, combinação com busca, transparência pública das tags, regressão e publicação.

Contrato para continuidade: `docs/TOPICS-V1-CONTRACT.md`. Catálogo e matriz podem ser reutilizados estruturalmente por outras frentes, mas as associações individuais nunca devem ser copiadas entre candidaturas.

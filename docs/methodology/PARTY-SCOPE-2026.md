# Recorte partidário canônico — Eleições 2026

O projeto passa a manter uma única lista verificável para os cargos de deputado federal e deputado estadual:

**PCB, PCdoB, PCO, PDT, PSB, PSOL, PSTU, PT, PV, REDE e UP.**

A regra é operacional: um registro entra no universo do projeto quando a sigla registrada no TSE pertence à lista. Isso não atribui, por si só, posição, pauta ou avaliação individual ao candidato.

## Regras

1. A mesma lista é verificada nos cargos 6 (deputado federal) e 7 (deputado estadual).
2. Uma sigla sem candidatura na UF/cargo permanece no relatório com valor zero.
3. Nenhuma sigla pode desaparecer apenas porque o resultado é zero.
4. Inclusões e exclusões são comparadas pelo identificador SQ_CANDIDATO, não por nome.
5. Situação eleitoral é uma dimensão separada do recorte: renúncia, indeferimento, recurso ou substituição não alteram silenciosamente o universo auditado.
6. Pautas individuais continuam dependendo de evidência individual; filiação não gera tags automaticamente.

A fonte eleitoral utilizada pela auditoria é o conjunto público Candidatos — 2026 do TSE. O relatório party-scope-audit.json registra hash do ZIP, hash do CSV por UF, contagens por sigla e IDs ausentes/excedentes nas bases do projeto.

A frente estadual do RS ainda é comparada em sua branch própria feat/rs-deputados-estaduais até a integração correspondente.

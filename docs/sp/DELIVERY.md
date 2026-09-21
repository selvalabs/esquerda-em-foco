# SP — entrega do Round A

## Resultado

Base eleitoral reconciliada: **PASS** para a fotografia do TSE gerada em **21/09/2026 às 12:31:37**, coletada em **21/09/2026 às 14:44:51–52 (UTC−03:00)**. São **1.131** registros de deputado federal em SP: **234** no recorte partidário herdado de SC/RS e **897** fora desse recorte, identificados no arquivo de auditoria. O recorte não é uma classificação ideológica de todos os partidos.

Situações dos 234 registros: 212 DEFERIDO; 1 DEFERIDO EM PRAZO RECURSAL OU COM RECURSO; 2 INDEFERIDO; 13 INDEFERIDO EM PRAZO RECURSAL OU COM RECURSO; 6 RENÚNCIA. As 22 situações diferentes de DEFERIDO foram preservadas. A expressão oficial “em prazo recursal ou com recurso” não foi reduzida a “recurso apresentado”.

## Verificação realizada

A execução [35633947022](https://github.com/selvalabs/esquerda-em-foco/actions/runs/35633947022) terminou com sucesso em todos os passos de coleta, validação e gravação da branch. Os **15 testes unitários passaram**.

O artefato `10655198663` foi baixado e aberto para uma segunda verificação, fora do runner. SHA-256 do ZIP original:

`42ad3e69521acc1a4d98029d64e0a62f7cbd6647249882ec08f7b0178dd9750c`

Conferências adicionais: os 16 hashes de arquivos enumerados em `checksums.json`; validação do JSON Schema; comparação de todos os 234 registros normalizados com os respectivos extratos de candidatura e de julgamento, incluindo nome, número, partido, situação e localizadores; partição exata do universo 1.131 = 234 + 897; votos/resultados de 2026 nulos; ausência de biografias ou pautas atribuídas nesta rodada. **Todas passaram.**

A reconciliação automática comparou o arquivo SP com o arquivo BRASIL do mesmo ZIP e cruzou os identificadores com as informações complementares. Não houve IDs duplicados, complementos ausentes, números de urna repetidos ou conflitos bloqueantes. Essas são exportações do mesmo sistema eleitoral, não duas instituições independentes.

Foram conferidos **330 arquivos preexistentes**, sem alterações. A comparação do baseline `810a7896b3355254d50852761a41bae31ce3f567` com `d688974aa7e268f538b182e9ba72595e6278fa8a` mostrou apenas 19 arquivos novos nos caminhos de SP e no workflow exclusivo desta frente. Este documento acrescenta somente o registro da entrega.

## Estado do código e do produto

Branch: `feat/sp-federais-round-a`. Issue: #8. Nenhum merge, deploy, rota SP, alteração de menu ou edição de SC/RS/PR foi executado.

O workflow temporário que aplicou a correção dos marcadores `#NE`/`#NULO` foi simplificado após o teste aprovado; a correção já está incorporada ao script Python. O código de coleta não mudou após a execução aprovada. A versão simplificada do YAML foi validada sintaticamente e comparada ao blob GitHub `c33c080d73406a6765f5722b8f9ae492f0887c93`; não houve nova coleta após essa limpeza. Pushes no código `tools/sp/**` podem executar novamente a coleta na branch exclusiva.

## Dependência que permanece

A lista eleitoral está fechada **para esta fotografia**, não para atualizações futuras do TSE. A taxonomia revisada de pautas de SC não estava homologada na referência consultada. `data/sp/taxonomy.lock.json` documenta a dependência: resolver a versão compartilhada antes de classificar candidatos no Round B. O Round A não aprova uma taxonomia nova de SP.

Biografias, histórico, mandatos atuais, fotos, redes, municípios de atuação e pautas individuais continuam marcados como não pesquisados. Os links de perfil do DivulgaCand seguem a rota utilizada pelo projeto, sem checagem HTTP individual. Não se deve interpretar campos vazios como ausência de trajetória, pauta ou candidatura anterior.

## Reutilização

`data/sp/normalized.json` é a base normalizada; `data/sp/candidates.csv` é a lista para conferência; `data/sp/exceptional-statuses.json` identifica as situações excepcionais; `docs/sp/ROUND-A.md`, `reconciliation.json` e `data/sp/manifest.json` registram o método, resultados e fontes.

Para testar o script: `python tools/sp/round_a.py --self-test`. Para recolher, executar `python tools/sp/round_a.py` na raiz de um checkout completo deste repositório, com acesso à internet e ao commit de referência. O pacote desta etapa é um recorte de dados/código/documentação, não um site pronto para deploy.

# SP federais — entrega parcial do Round B

**Data: 21/09/2026. Validação técnica: PASS. Pesquisa editorial: PARCIAL. Publicação: NÃO LIBERADA.**

O enriquecimento oficial e o primeiro conjunto de pesquisas individuais estão versionados. O Round B completo ainda não está encerrado: 189 dos 234 registros não receberam pesquisa editorial individual, e as 45 entradas existentes têm profundidades diferentes e lacunas registradas.

## GitHub

Repositório: `selvalabs/esquerda-em-foco`. Branch: `feat/sp-federais-round-a`. Tarefa: [issue #12](https://github.com/selvalabs/esquerda-em-foco/issues/12). Referência eleitoral: issue #8 e commit `b42f2e1f108185c7f9c3d5af7e5e92e893aef574`.

Código, testes e cinco arquivos de pesquisa: `3c31d7136a736bc41d4a7f1506207a128d3c7356`. Dataset e auditoria gerados: `44638da514a8ee0119bb9eea6aa0084e0664e846`.

[Execução GitHub Actions 35640520991](https://github.com/selvalabs/esquerda-em-foco/actions/runs/35640520991): todos os passos concluídos com sucesso, incluindo os 24 testes e a checagem de isolamento. A documentação desta entrega foi acrescentada depois, sem mudar o código ou a base testada.

## Dados oficiais

| Item | Cobertura |
|---|---:|
| Registros do Round A preservados | 234 |
| Perfis individuais conferidos no DivulgaCand | 234 |
| Fotografias oficiais vinculadas por identificador | 234 |
| Pessoas com redes/sites declarados ao TSE | 215 |
| Pessoas com candidaturas anteriores a 2026 no arquivo histórico | 176 |
| Registros históricos anteriores a 2026 | 555 |

A identidade foi conferida por ID, nome civil e número. As fotos tiveram identificador, hash e integridade de arquivo verificados; isso não é uma revisão visual de cada retrato. Os links sociais foram coletados das declarações e verificados sintaticamente, não visitados individualmente em sua totalidade.

Foram separadas 81 linhas do próprio pleito de 2026 presentes no arquivo histórico. Por isso, a contagem inicial de 206 pessoas com qualquer linha nesse arquivo não representa o número com candidaturas anteriores. Votos históricos não foram coletados e continuam nulos; os votos e resultados de 2026 também continuam nulos.

A coleta inicial ocorreu entre 15h10 e 15h13 de 21/09/2026, no horário de Brasília. A verificação complementar ocorreu entre 15h19 e 15h23. Datas de geração dos arquivos do TSE, URLs, hashes e localizadores estão em `collection.json`, `supplement.json` e nos registros derivados.

## Pesquisa individual

| Item | Resultado neste checkpoint |
|---|---:|
| Entradas individuais de pesquisa ou triagem nominal | 45 |
| Candidaturas com alguma fonte editorial lida | 34 |
| Biografias curtas aceitas com atribuição de fonte | 33 |
| Candidaturas com evidência temática aceita | 21 |
| Relações candidato–tema–evidência–fonte | 50 |
| Fontes editoriais registradas | 47 |
| Observações institucionais sobre exercício de cargo | 3 |
| Registros sem pesquisa editorial individual | 189 |

Essas contagens não devem ser somadas: as categorias se sobrepõem. Uma fonte profissional foi mantida como observação com identidade pendente, sem biografia aceita ou pauta atribuída. As outras entradas sem conteúdo aceito registram buscas e lacunas, não ausência de atuação política.

Sites de candidatos e perfis partidários são apresentados como declarações dessas fontes. Dados legislativos distinguem autoria, coautoria, relatoria e declaração pública. A leitura de algumas biografias institucionais se limitou ao trecho indexado oficial, identificado no campo `retrieval`; não se afirma leitura integral nesses casos.

## Taxonomia e filtros

Fixada a versão `1.0.0-documental`, com 29 famílias temáticas mapeadas à proposta de SC no commit `c2ce0d44f64c72c5949d373fa210d9144948d310`. A categoria Saúde não implica automaticamente defesa de toda medida relacionada ao SUS.

É um contrato para pesquisa documental, não homologação de filtros ativos para todas as UFs. Cada relação inclui medida, direção/atribuição, temporalidade e fonte. Nenhuma posição foi atribuída apenas por partido ou profissão. As associações de apoio atual permanecem desativadas; a interface não foi alterada.

## Validação adicional do pacote

O artefato `10658555172` foi baixado e validado fora do runner. SHA-256 do ZIP original:

`cfc27e66073d2ddf4b1316290c8c5cacb66931d4d569b26c11d0448baa717bf3`

Foram conferidos 259 hashes do manifesto, sete blobs de código/testes/entradas e seis saídas determinísticas, idênticas ao processamento local. O JSON Schema passou; os 234 arquivos de imagem foram abertos para verificação estrutural; os 555 registros históricos normalizados foram cotejados com o extrato sanitizado. Os 24 testes passaram novamente sobre o pacote baixado. Registro: `INDEPENDENT-VALIDATION.json`.

O inventário original de hashes cobre a saída do workflow; este documento e a validação independente foram acrescentados posteriormente. O ZIP de entrega inclui inventário próprio atualizado.

## Preservação e pendências

O inventário inicial conferiu 349 arquivos preexistentes sem alteração. A checagem final do workflow restringiu as mudanças aos caminhos de B e aos workflows exclusivos de SP. O único ajuste no workflow de A foi estreitar o gatilho para impedir que alterações em B recoloquem a fotografia eleitoral. Nenhum dado de A, frontend ou arquivo de SC/RS/PR foi alterado. Não houve merge ou deploy.

A API da Câmara expirou mesmo após tentativas registradas. Isso não significa que os candidatos sem correspondência nunca exerceram mandato. Observações obtidas nas páginas públicas da instituição têm fontes próprias. O erro inicial do parser do DivulgaCand foi corrigido, preservando o registro da tentativa anterior e repetindo a verificação dos 234 perfis.

Uma situação usa redações diferentes no extrato eleitoral e no perfil do DivulgaCand. Ambos os textos e suas fontes foram preservados em `audit.json`, sem alterar retrospectivamente o Round A ou inferir que prazo recursal equivale a recurso apresentado.

Para encerrar o Round B, falta pesquisar os 189 registros ainda sem entrada, aprofundar as fichas parciais, resolver confirmações de identidade e cargos atuais e conferir os links individuais. A fila nominal está em `research-queue.json` e `coverage.csv`. Ausência de evidência localizada não representa oposição a uma pauta.

## Arquivos e reprodução

Dados em `data/sp/round-b/`; relatórios em `docs/sp/round-b/`; scripts em `tools/sp/round_b/`; testes em `tests/sp/round_b/`.

Com os arquivos de A e B na estrutura do repositório, executar `python tools/sp/round_b/build.py` e depois `python -m unittest discover -s tests/sp/round_b -v`. Essa reconstrução não requer internet. A coleta original depende de checkout Git completo, referências upstream e acesso às fontes oficiais; não é executada implicitamente quando a coleta congelada já existe.

Este pacote é um checkpoint de dados, pesquisa e código, não um site pronto para publicação.

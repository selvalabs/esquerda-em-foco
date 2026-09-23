# Transparência legível — D3 / #55

A proveniência é um vínculo verificável, não um selo de que toda afirmação é
verdadeira. A reorganização não recolhe dados do TSE, não atualiza mandatos e não
muda a data de documentos. Usa a baseline `9dbb26d506a01ddc2dab01bb70611095f1d5a3f8`.

## Contrato

A chave `edição:ID` identifica uma candidatura numa eleição/UF/cargo. Não representa
uma pessoa universal e não permite fundir registros por nome. A leitura mostra
cargo, estado e eleição; códigos/hashes ficam no modelo de auditoria.

Cada observação acrescentada tem valor original, caminho, SHA-256, JSON Pointer
ou seletor do HTML e hash do valor. O validador resolve novamente esses locais
nas fontes. Não confundir o localizador do repositório com o localizador de uma
fonte externa: este último só é mostrado quando realmente consta do registro.

A evidência conserva texto, tema nativo, natureza, direção, objeto quando
estruturado, atribuição, período e fontes pertinentes. Metadado ausente permanece
nulo e é explicado como não informado. Nenhum título global de tema transforma
uma associação em elegível; `global_filter_activation` permanece falso neste
protótipo. A #56 aplica o contrato da #53 mediante relações revisadas.

## Semânticas mantidas

SC conserva as decisões individuais `eligible_v2`, sem promover registros
históricos/oposições/contextos. SP mantém evidências como posições/atuação
documentadas. Sínteses SC Estadual/RS/PR conservam a granularidade de **síntese
inteira**: não se inventa uma fonte específica por frase. O painel torna esse
limite visível, junto dos documentos de origem.

Uma fonte de campanha continua sendo declaração atribuída. Um registro legislativo
não comprova execução. Datas de publicação, consulta e período da afirmação são
campos separados. Sem data não quer dizer antigo; uma consulta de setembro não
transforma conteúdo anterior em programa de 2026.

## Cadastro, mandato e histórico

A situação cadastral é separada do campo de aptidão. Quando este não foi fornecido,
não se calcula aptidão a partir de “deferido”. Campos de recurso e conflitos de
origem são preservados no modelo e na apresentação original.

SC Estadual distingue registro institucional, declaração própria, atividade datada,
licença, suplência e não confirmação. As observações de mandato de RS/PR/SP
mantêm o texto e a fonte datados: não se convertem, só pela existência de URL, em
uma nova confirmação de exercício. Ausência de documento não comprova ausência
de mandato. Uma lista de legislatura não cobre automaticamente licenças.

Histórico anterior vinculado, nenhuma disputa anterior num conjunto coberto e
histórico não coletado são diferentes. Os 15 registros SP explicitamente não
coletados continuam assim. A eleição de 2026 não é computada como anterior.
A carreira SC Federal ainda reside parcialmente no HTML: preserva-se esse
contexto, sem extrair totais ou comprovar mandato por palavras da narrativa.

Votos verificados nominais exigem inteiro não negativo. Zero é válido apenas
quando o estado documental o permite. Valor sem estado suficiente permanece
“informado sem classificação”, não vira verificado. `null`, não coletado, não
verificado, não aplicável e não publicado não são convertidos em zero. As linhas
históricas conservam contexto de cargo, circunscrição, turno e eleição.

## Cobertura e correções

A presença de uma síntese é distinta da revisão completa da candidatura.
“Não pesquisado”, “não localizado”, “insuficiente”, “bloqueado”, “não consolidado”
e “não aplicável” possuem estados explícitos no contrato. Não são inferidos pela
quantidade de palavras ou fontes. As lacunas originais acompanham a ficha.

O contrato de correções aproveita a separação existente no PR #9, ref
`c2bfa3ece357f21e8aa09e32f624a9e214ad9113`, em `rs/deputados-estaduais/revisoes.json`:
registro anterior, retirada, motivo, data, fontes e ponto não resolvido. Uma retirada
não volta a contar como atuação atual. A branch não é incorporada/publicada nesta
etapa; a regra é testada com fixture sintética fora das páginas.

## Segurança e limites

Texto adicional é escapado, URLs explicativas aceitam HTTP/HTTPS sem credenciais,
e IDs de fonte incluem a candidatura/edição. Não há chamadas a analytics, cookies,
localStorage ou backend. O script novo só organiza a leitura da evidência.

Não foi feita nova verificação externa da verdade das afirmações políticas.
A validação demonstra consistência com as fontes versionadas, preservação e
funcionamento do protótipo, não uma certificação eleitoral ou de acessibilidade.

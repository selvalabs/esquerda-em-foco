# Cuidados de integridade encontrados na execução A–D

Corte da pesquisa: 21/09/2026. Estes ajustes pertencem somente à frente RS/estaduais.

## Um identificador antigo não basta

Na extração de 2004, o mesmo identificador de candidatura apareceu em municípios diferentes. Por isso, o cruzamento usa o vínculo oficial do histórico e confere unidade eleitoral, ano, cargo, turno, número e nome civil. A auditoria guarda a quantidade de linhas excluídas por pertencerem a outro contexto. A coincidência de nome, sozinha, nunca foi usada para recuperar votos.

As evidências estão em `data/rs-estaduais/votes-phase2.json` e `docs/rs-estaduais/phase2/votes-audit.json`. O primeiro cruzamento que encontrou a incompatibilidade foi interrompido; o erro permanece no histórico da auditoria, seguido das tentativas com validação mais estrita.

## Município da linha de votação versus circunscrição da disputa

A fonte do TSE para 2010 é uma tabela de votação nominal por município e zona: <https://dadosabertos.tse.jus.br/dataset/resultados-2010>.

Nas linhas de deputados examinadas, `SG_UE` traz códigos municipais, enquanto o histórico oficial vincula a candidatura à circunscrição `RS`. O coletor tem uma regra explícita e limitada à fonte de 2010: aceita a granularidade municipal somente quando `SG_UE` é igual a `CD_MUNICIPIO`, `SG_UF` é `RS`, o cargo é deputado federal ou estadual e o vínculo histórico é estadual. Ano, turno, número e nome civil continuam sendo conferidos.

Essa regra não se aplica a prefeito, vereador, outra UF ou outro ano. Os valores originais de exemplo, a circunscrição efetiva e as contagens por regra permanecem em `source_unit_examples` e `source_unit_basis_counts`. Não se atribui automaticamente um código municipal qualquer ao Rio Grande do Sul.

## O que um nulo significa

A coluna `votes_status` distingue votação nominal conferida, registro sem correspondência segura, população eleitoral não coletada, turno desconhecido e situações em que votação nominal própria não se aplica. Vice e suplência não são incluídos na fila de recuperação de votos nominais individuais. Nenhum `null` foi convertido em zero.

O ZIP nacional é acessado por intervalos HTTP; por isso, o hash do arquivo nacional permanece nulo. O membro RS é integralmente lido e validado por tamanho, CRC e SHA-256. Não se confunde um hash de trecho com hash de arquivo completo.

## Uma lacuna antiga não apaga uma descoberta posterior

A reexecução da camada editorial revelou que uma entrada antiga com `pautas: null` conflitava com uma síntese acrescentada depois. O merge foi corrigido para manter a informação revisada mais recente quando o insumo anterior apenas registrava ausência de conhecimento.

Isso não permite substituição silenciosa: dois textos não vazios e diferentes continuam gerando erro. Remoções e correções substantivas precisam de alteração editorial explícita. Testes exercitam a repetição da fase anterior seguida da nova fase e verificam que textos, fontes e atos não se perdem nem se duplicam.

## Alcance da validação

Os testes de regressão destas regras não substituem a revisão editorial final E nem a atualização eleitoral e decisão de publicação F. Os relatórios A–D discriminam cobertura alcançada e pesquisas ainda pendentes; a issue #5 e o PR #9 não devem ser encerrados automaticamente.

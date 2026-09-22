# Filtros globais: vocabulário, evidência e disponibilidade

**GLOBAL-04D1 / issue #53**, filha da #43, epic #39. Baseline: `60f4d533d55e07f5a56847adb09a8a88fec37938`.
Estado desta entrega: **contrato especificado e testável; não ativado no site**.
A #50 continua fora desta execução. Ficha/editorial e transparência seguem nas
#54/#55; aplicação nas seis edições, na #56; reconciliação, na #57.

## Decisão principal

O produto terá **um sistema de filtros global por composição**. Não terá um
modelo SC copiado integralmente, nem seis modelos locais tratados como solução
final. O que varia é a evidência disponível e a etapa de migração, não o objetivo
de oferecer a mesma organização de consulta.

A gramática comum é: **Busca → Partidos → Temas e evidências → Situação eleitoral
→ Mandato → Histórico eleitoral → Localidade documentada → Ordenação**.
Campos não utilizáveis devem ter motivo explicado; dados incompletos numa dimensão
não desativam as outras. Não confundir zero correspondências com função indisponível.
No mobile, os grupos podem ser recolhidos e ter resumo dos critérios, sem empilhar
39 botões permanentemente. O catálogo completo continua acessível; número de
temas não é meta de quantidade de controles abertos na tela.

## O que foi conciliado

O catálogo `config/taxonomies.json` conserva 29 entradas SC, 30 SP, 28 RS e 25 PR:
**112 entradas locais**, com sobreposição. O novo vocabulário contém **39 temas**,
organizados em **16 grupos de navegação**. Não é um inventário exaustivo de políticas.

Os 29 domínios com definição de inclusão/exclusão já compartilhada por SC/SP foram
mantidos. Ciência, tecnologia e inovação de SP entra como domínio explícito.
Outros nove domínios preservam recortes de RS/PR que não podem sumir dentro das
rubricas de SC: consumidor; esporte e lazer; liberdade religiosa; previdência;
direitos sociais; trabalho/emprego/renda; desenvolvimento regional e indústria;
renda e proteção social; segurança alimentar.

O crosswalk tem **58 registros de equivalência de definição** (29 SC para o
contrato e as 29 definições idênticas SP), **44 relações de escopo delimitado**
para os vocabulários curtos RS/PR e **10 contribuições específicas** (uma SP, sete
RS, duas PR). São registros de mapeamento, não 58 temas diferentes nem quantidade
de candidaturas. Cada entrada tem fonte, hash, localizador e exemplos reais de
uso no repositório. Nenhuma associação de candidatura foi escrita por esse mapa.

`related` não é um eufemismo para equivalência. Os catálogos RS/PR possuem rótulos,
mas não as mesmas definições extensas de inclusão/exclusão. Sua ligação ao domínio
global foi delimitada explicitamente; **o objeto nativo deve aparecer junto da
correspondência**. Rubricas sobrepostas, como trabalho/direitos trabalhistas e
moradia/regularização fundiária, exigem leitura do objeto por afirmação antes de
transportar associações. Isso não impede o desenho comum; impede extrapolação.

O documento [GLOBAL-FILTER-CROSSWALK.md](GLOBAL-FILTER-CROSSWALK.md) enumera as 112
linhas. `filter-crosswalk.json` é a versão auditável, com os mesmos resultados e
**oito atalhos rejeitados ou dependentes de revisão individual**. Um vínculo novo
pode existir se houver outra evidência; não se obtém por transitividade entre temas.

## Assunto não é concordância

A interface global usa o cabeçalho **Temas e evidências**, com três recortes
explicitamente diferentes:

| Recorte | O que significa | O que não permite concluir |
|---|---|---|
| Apoios e prioridades documentados em 2026 | Defesa positiva, atribuída individualmente e com contexto atual revisto | Toda medida possível dentro do tema; oposição convertida em apoio |
| Posições e atuação documentadas | Declaração, oposição ou atuação com vínculo individual e fonte pertinente | Que uma atuação histórica seja promessa atual, ou que citar um assunto seja apoiá-lo |
| Contexto temático da pesquisa | Associações herdadas, cuja estrutura ainda não permite a mesma leitura por afirmação | Atualidade, apoio ou completude inferidos pelo rótulo |

A visualização global neutra deve caminhar para **Posições e atuação documentadas**,
com recorte positivo disponível separadamente. A elegibilidade positiva SC pode
aparecer também na visualização neutra sem mudar seu sentido. Isso não habilita
automaticamente as demais afirmações SC, SP ou PR: o adapter precisa preservar
as decisões individuais e as lacunas. Material legado continua identificado
separadamente até a revisão por afirmação prevista nas #54/#55.

Natureza, direção e período são eixos diferentes: uma declaração pode ser antiga;
uma notícia de 2026 pode falar de ato de 2023; uma consulta feita em setembro não
data o ato. Um projeto antigo só é apresentado como prioridade atual com reafirmação
documentada. **Sem data não significa antigo; fonte bloqueada não significa que
não existe posição; oposição não significa ausência de pauta.**

Uma defesa ampla de Saúde é evidência válida de prioridade ampla. Não é obrigatório
inventar mecanismo ou exigir projeto de lei para reconhecê-la. Também não permite
acrescentar SUS, cannabis, enfermagem ou qualquer objeto não expresso.

## “Qualquer” e “Todos” é o padrão global

Partidos combinam por **OU**. Dimensões independentes combinam por **E**. Temas
oferecem **Qualquer / Todos**, com “Qualquer” como padrão de consultas novas.
Dentro de um grupo, basta uma evidência elegível de um dos temas filhos; ela não
produz apoio aos irmãos. “Todos os grupos” exige evidência para cada grupo.

**PR pode receber “Qualquer” sem pesquisa política nova**: é a união dos vínculos
existentes, não a criação de vínculos. O impedimento atual é implementação e
compatibilidade, não uma impossibilidade semântica do OU. Seu motor atual continua
com E até a #56, e um link PR antigo continua significando “Todos”. A semântica
`legacy_context` desses resultados não muda ao adicionar o operador.

Contagens usam chaves distintas `edição:candidatura`, não quantidade de fontes ou
de afirmações. O total mostrado num botão deve explicitar se é o universo não
filtrado; o total de resultados deve corresponder à consulta inteira. Combinar
um grupo e um filho em “Todos” não dá peso dobrado: o filho é a restrição mais
específica. Não há ordenação por afinidade, temas, cobertura ou popularidade.

## Links antigos: significado congelado

SC usa 14 macrogrupos de origem, 13 com resultados no painel publicado da baseline.
O contrato registra **os 14**, inclusive o sem correspondência. Seus membros ficam
congelados em `legacy_group_queries`: uma consulta antiga por Agricultura não ganha
Segurança alimentar só porque o grupo global novo reúne ambos; Cultura não ganha
Esporte, e Trabalho não ganha todas as políticas de renda/previdência.

O antigo grupo Ambiente/animais continua uma cláusula OU das três famílias originais,
mesmo que no desenho novo elas estejam em dois grupos. Transformar essa cláusula
em E alteraria o resultado de um link. Aliases de três IDs SP estão registrados
exatamente como na proveniência original, separados de sinônimos de pesquisa.

Os links `eef=query&v=1` e as coleções não são modificados nesta entrega.
A seleção de vocabulário global requer transporte novo com versão da taxonomia,
edição/eleição, recorte, seletores e operadores; a proposta é **consulta v2**, na #56.
Não confundir essa versão com a coleção v2 já publicada. Importação antiga não
muda silenciosamente o universo ou o significado. Compartilhar continua explícito.

## Dados presentes não são funcionalidades ativadas

A matriz [filter-capabilities.json](../data/global-integration/filter-capabilities.json)
registra **disponibilidade dos dados**, **implementação corrente** e **bloqueio**
separadamente. A leitura dos exports da baseline revelou oportunidades concretas:

| Frente | Dados já disponíveis na baseline | Trabalho que continua necessário |
|---|---|---|
| SC Federal | Pautas e decisões por associação; carreira/identificação no HTML | Adapter de cadastro/mandato/histórico, sem tratar flags de DOM como comprovação |
| SC Estadual | 13 registros de mandato com fonte institucional; 77 fichas com pleito anterior vinculado | Separar mandato e histórico em controles independentes; matriz temática não pode ser inferida da síntese |
| RS Federal | 17 objetos de mandato com fonte; 84 fichas com pleito anterior; status e 64 fichas com vínculos temáticos | Ativar controles a partir dos dados existentes; tipificar evidências antes de filtro de posição/tempo |
| PR Federal/Estadual | Mandatos com fonte em 10/3 fichas; histórico anterior em 82/108; localidade com fonte em 1/3 | Aplicar gramática comum, OU/E e critérios de desconhecido sem promover os temas legados |
| SP Federal | 3 observações de mandato com fonte; 176 fichas com histórico anterior | Adapter de mandato/histórico; 15 registros têm histórico explicitamente não coletado, não são “estreantes” |

Essas são **contagens de campos no snapshot**, não validação externa atual dos
mandatos nem comparação de qualidade política. Os registros e seus localizadores
estão no JSON. Para SC Federal, contagens não calculáveis do export semântico são
`null`, não zero; a presença de dados no HTML foi registrada separadamente.

Situação cadastral, recurso e aptidão no snapshot são dimensões distintas.
Não calcular aptidão apenas pelo nome do status de deferimento. Conservar a fonte,
a data e conflitos; desconhecido não equivale a inapto.

Mandato não é um booleano universal: registro institucional, exercício confirmado,
declaração própria, não exercício comprovado e falta de confirmação são diferentes.
O `false` legado significa **sem confirmação**, não prova de ausência. Uma composição
institucional também não descreve automaticamente todas as licenças. Eleição
anterior não é mandato atual.

Histórico distingue disputa anterior vinculada, nenhuma anterior num snapshot
coberto e coleta não estabelecida. O pleito de 2026 é excluído ao testar disputa
anterior. Votação nula, zero nominal verificado, não coletada e não aplicável não
são intercambiáveis. A falta de votação não impede consultar um histórico com
cargo, ano e fonte; apenas impede preencher o número.

Localidade significa **atuação documentada com lugar e fonte**, não residência,
base eleitoral ou representatividade inferida. Ordenação alfabética é um recurso
que pode ser globalizado sem coleta nova; a rotação diária permanece neutra, com
fuso de Brasília e regras legadas preservadas até migração deliberada.

## Identidade e explicação visível

`eleição + UF + cargo + ID` identifica uma candidatura no contexto de uma edição,
**não uma identidade universal de pessoa** entre cargos ou anos. Não juntar por
nome. A #55 deve transformar os metadados úteis em cargo/estado/eleição, data e
origem compreensíveis, não expor hashes como conteúdo principal.

Para “por que aparece aqui?”, preservar: assunto de origem, domínio global,
objeto/trecho, atribuição, natureza, direção, período, fonte pertinente e lacunas.
Exemplo de estrutura, não de afirmação política nova:

> Aparece em Mobilidade por este projeto sobre transporte, documentado na fonte
> indicada. É uma atuação de 2024; isso não confirma uma prioridade de 2026.

O leitor pode expandir a fonte e o contexto completo. Informação ausente permanece
explícita. Não anexar todas as fontes de uma ficha a toda frase; não transformar
um grupo de navegação numa recomendação. A mesma ficha original continua sendo
usada no leitor de Selecionados.

## Entregáveis e testes

- `config/global-filter-taxonomy.json`: 39 temas, 16 grupos e políticas globais;
- `config/global-filter-taxonomy.schema.json`: schema de contrato, crosswalk e matriz;
- `data/global-integration/filter-crosswalk.json`: 112 mapeamentos, aliases, compatibilidade de grupos e atalhos vedados;
- `data/global-integration/filter-capabilities.json`: situação por edição/dimensão;
- `data/global-integration/filter-inputs.json`: fontes, hashes e baseline;
- seção aditiva `canonical_filter_contract` em `migration-status.json`, sem alterar o histórico dos lotes 01/02;
- `tools/global_filters/contract.py`: especificação executável isolada, **não motor já ligado ao site**;
- testes de schema, fontes, não promoção, contagens, grupos, identidade e preservação.

```bash
python tools/global_filters/build.py --check
python tools/global_filters/schema.py --check
python -m unittest discover -s tests/global_filters -p 'test_*.py' -v
python tools/global_filters/verify_preservation.py --out /tmp/d1-preservation.json
```

O build recusa fontes que mudaram desde o manifesto até uma revisão explícita.
A comparação Git cobre os arquivos anteriores contra o main congelado, com a
única exceção da seção aditiva no status de migração. Não requer rebuild de HTML,
coleta TSE ou nova pesquisa de posições políticas. Não confundir sucesso destes
testes com rollout visual, teste em aparelho ou rechecagem externa das fontes.

## Handoff para #54, #55 e #56

#54/#55 devem trabalhar juntas na **ficha composta e transparência visível**, usando
este vocabulário e preservando textos/objetos já revisados. O contrato não autoriza
redigir síntese política artificial nem escolher SC inteira como molde. Metadata
incompleta deve aparecer como tal. Depois a #56 aplica gramática, operadores,
versionamento e adapters nas seis edições, testando cada funcionalidade com o
conjunto exato de registros e o leitor original. #57 reconcilia a migração; #44
fecha a regressão global. RS Estadual mantém seu gate próprio; #50 fica para depois.

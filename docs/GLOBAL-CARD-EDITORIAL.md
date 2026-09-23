# Ficha canônica composta — D2 / #54

Status: contrato e protótipo isolado; a ativação pública pertence à #56.
Trabalho conjunto com D3 / #55, sob a #43 e o epic #39. A #50 não entra neste round.
Baseline: `9dbb26d506a01ddc2dab01bb70611095f1d5a3f8`.

## Decisão de leitura

A ficha começa pela pessoa candidata, pelo cargo, estado e eleição, e por **O que
encontramos**. O texto corrente conserva sua autoria, cautelas e fontes. A leitura
não exige abrir um registro técnico para entender o que foi documentado.

**Mandato e histórico eleitoral**, **Canais públicos e endereços declarados**,
**De onde vêm estas informações?** e **Ler as evidências e seus limites** são
camadas de aprofundamento. A ficha não recebe um parágrafo genérico para cobrir
uma lacuna. Não há tamanho padronizado nem nota de afinidade ou completude política.

Os títulos internos que distinguem pautas, atuação e contexto nas versões de
origem permanecem. A estrutura composta não significa renomear toda atuação como
pauta atual. Fonte e ressalva continuam próximas do texto que qualificam.

## Preservação por contribuição

| Origem | Incorporar | Não transportar automaticamente |
|---|---|---|
| SC Federal | Parágrafos legíveis, associação por trecho, itens de evidência, cautelas de atribuição e duas datas (pesquisa/redação) | Apoio para todo um grupo porque uma família teve evidência; data de redação como pesquisa nova |
| SC Estadual | Trajetória pública/eleitoral, situação oficial, documento do mandato, licença, suplência e canais declarados | Falta de confirmação como ausência de mandato; página partidária como fonte independente |
| RS Federal | Texto contextual, natureza do registro, fonte datada e estados dos votos | Restaurar uma síntese antiga que a revisão posterior substituiu; anúncio/proposição como execução |
| PR | Síntese, cadastro separado, fontes e localidade documentada | Fonte da síntese como suporte automático de toda frase; localidade como domicílio |
| SP | Afirmação tipificada, fontes pertinentes, período, biografia atribuída e evidência focalizada | Converter todas as declarações/atuações de 2026 em apoio atual; histórico não coletado como estreia |
| RS Estadual, branch | Contrato de correção com antes/motivo/fonte e pesquisa separada de conclusão | Publicar a branch ou tornar novamente vigente uma atribuição retirada |

## Mais de uma versão escrita

O relatório `audit/editorial-reconciliation.json` do protótipo possui uma entrada
para cada uma das 760 fichas. Em SC Federal relaciona o conteúdo semântico com a
redação editorial e a página efetivamente publicada. Os itens documentais não
são substituídos por uma paráfrase: permanecem acessíveis em suas estruturas de
origem, com os mesmos IDs. Em RS Federal compara a baseline editorial com a
revisão corrente. As diferenças ficam localizadas por arquivo, hash e chave.

Uma redação anterior não é reinserida só porque é mais extensa. Onde há mudança
substantiva, a precedência é da revisão atual; a versão antiga continua preservada
no acervo e no registro comparativo. Reaproveitar uma alegação retirada requer
revisão individual da fonte. O protótipo não faz nova investigação política.

Nos demais estados a comparação liga o export público revisado e o HTML corrente.
Este inventário cobre esses arquivos explícitos; não declara ter examinado toda
a história de commits do repositório. O resultado não é uma reescrita de 760
sínteses: é preservação e composição verificável dos textos e seus contextos.

## Implementação

`tools/canonical_cards/model.py` adapta os exports já existentes sem mutação.
`render.py` move nós originais para uma estrutura comum e acrescenta observações
rastreáveis. `card.css` é o vocabulário visual compartilhado; `card.js` permite
focalizar evidências por tema sem ocultar permanentemente o restante do contexto.
Não cria um segundo motor de busca nem altera associações.

O leitor de Selecionados continua movendo o mesmo `article`, não uma cópia. IDs,
links externos, fragmentos, atributos de consulta e textos originais são comparados
antes/depois. Os estados de filtros e as coleções continuam por edição/ano.

Apenas no pacote isolado, o indexador SC ignora os novos rótulos explicativos,
para eles não se tornarem falsos termos de busca. A modificação é feita por um
adapter com âncora validada; o runtime público permanece intacto.

## Protótipo e aplicação posterior

O build gera seis páginas completas, uma galeria de 18 casos técnicos e os
relatórios fora do repositório. Todas as páginas de ensaio são `noindex`; o pacote
não é um deploy do produto. O site publicado, as capabilities e os snapshots não
são alterados nesta fase. A #56 liga o renderer à cadeia de refresh e faz o rollout
com baseline renovada e testes de publicação.

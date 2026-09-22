# SC Federais — interface semântica v2

Issue #32, Round 2. Implementação em 22/09/2026; recorte documental de 21/09/2026. Esta documentação descreve a implementação. A prova de publicação e os commits finais ficam no relatório de publicação, após o merge.

## O que muda

As 48 fichas permanecem disponíveis. Os cards passam a separar **Pautas defendidas**, **Posições públicas** e **Histórico de atuação**, somente quando o modelo aprovado contém conteúdo. Material sem período determinado ou atribuição confirmada aparece como **Contexto documental**, dentro de Fontes e contexto. Uma data ausente não é automaticamente tratada como documento antigo.

As 29 famílias documentais permanecem no catálogo. Os filtros mostram 13 áreas amplas com correspondências, dentre 14 grupos aprovados. Relações internacionais está preservada e explicada, mas não vira um botão sem resultados atuais. O painel inclui **O que cada filtro reúne**, com os 14 grupos e todas as famílias, para que LGBTQIA+, igualdade racial, deficiência, envelhecimento e outros assuntos não desapareçam dentro dos agrupamentos.

O resultado filtrado recebe **Por que aparece neste filtro**, com grupo, família, frase específica e fonte. A frase vem de `match_text`, sem um prefixo automático que atribua apoio a toda a categoria. Para Jú, a associação tributária é apresentada como **Defende impostos proporcionais à renda e ao patrimônio.** O mesmo grupo pode conter outros assuntos, sem que a candidatura receba associação a eles.

O novo recorte usa 112 associações elegíveis em 19 candidaturas. As 11 associações reclassificadas no Round 1 não alimentam mais filtros positivos; permanecem nos blocos correspondentes. Não houve nova pesquisa de candidaturas nesta implementação. As 19 lacunas documentais anteriores continuam sinalizadas, e não são o mesmo conjunto que as 19 candidaturas com correspondências atuais.

## Dados canônicos e saídas

Entradas somente de leitura:

- `data/sc-semantic-v2/association-audit.json` — elegibilidade v2, natureza, frase e fontes de cada associação.
- `data/sc-semantic-v2/candidate-content.json` — 48 fichas com resumos aprovados e evidências por bloco.
- `data/sc-semantic-v2/macrogroups.json` — grupo primário de cada uma das 29 famílias.
- `data/sc-semantic-v2/source-review.json` — referências, localizadores e limites da reconferência.
- `config/topics-v1.json` — nomes das famílias internas, sem alteração.

Saídas geradas:

- `index.html` — apenas áreas editoriais, índice de busca, metodologia e blocos marcados de filtros.
- `assets/sc-federais-filters-v2-data.js` — payload estático próprio da edição e da versão.
- `assets/pauta-filters-v2.js` — runtime v2 derivado do código v1 preservado, com checagem de hash e adaptação explícita.
- `data/sc-semantic-v2-ui/payload.json` e `manifest.json` — dados do frontend, contagens e hashes das entradas.
- `data/sc-semantic-v2-ui/qa.json` e `unit-tests.txt` — registros da preparação. O QA do merge candidato fica no artifact do run correspondente.

Os arquivos v1 continuam no repositório como proveniência, mas seus scripts de filtro não são carregados junto com os da v2. Seus flags de ativação e `data-has-pauta` não são usados para decidir a elegibilidade atual. O estado efetivo desta interface está no manifesto v2.

O CSS base e o motor puro de OR/AND são reutilizados sem alteração. `assets/pauta-v2.css` contém os ajustes da apresentação dos blocos e do painel. A separação entre blocos permanece mesmo depois de ocultar ou limpar o motivo de correspondência.

## Regras de funcionamento

O padrão **Pelo menos uma** aceita qualquer área selecionada. **Todas** exige uma associação própria em cada grupo. Contagens são uniões de pessoas, não quantidades de fontes ou afirmações, e representam o total da edição sem condicionamento à busca.

A busca textual combina com a seleção. Ela usa os resumos editoriais e a identidade/trajectória já existentes, sem incorporar a lista de metadados das fontes como se fosse pauta. O filtro temático não classifica o texto: usa os IDs aprovados. A rotação diária continua sendo a única responsável pela ordem.

No desktop, os filtros ficam abaixo dos partidos, em sidebar com rolagem interna. Até 980 px, o mesmo painel é deslocado para um diálogo nativo, sem duplicação de IDs ou estado. Há foco inicial, contenção de Tab/Shift+Tab, Escape, botão fechar, toque fora e devolução do foco. Os testes aguardam o evento assíncrono de fechamento antes de conferir o foco.

Limpar pautas conserva a busca. Limpar tudo, no estado vazio, remove os dois critérios. Links individuais revelam fichas ocultadas e informam a limpeza necessária. Referências numeradas abrem Fontes e contexto na referência correspondente; a seção opcional Ver evidências por bloco mantém os vínculos mais detalhados sem alongar todos os cards inicialmente.

Sem JavaScript, as 48 fichas e o conteúdo editorial já estão no HTML. Se o payload ou runtime de filtros falhar, os controles permanecem ocultos e a busca original continua disponível quando o JavaScript principal estiver funcionando. Um payload de versão incompatível não inicializa os filtros.

## Privacidade e implantação

As escolhas de pautas existem somente em memória: não são enviadas a uma API, incluídas em parâmetros de URL nem gravadas em cookies ou armazenamento local. O contador de métricas continua desativado. Este round não altera domínio, banco, VPS ou configuração de analytics.

O frontend é estático e funciona no GitHub Pages. Pode ser servido posteriormente na VPS com os mesmos arquivos e caminhos relativos; não exige backend para filtrar. O contador futuro continua sendo uma configuração separada.

CSS e scripts carregados no index possuem parâmetros de versão derivados de SHA-256. Isso reduz o risco de combinar o HTML v2 com um asset antigo em cache. A publicação é verificada por bytes e por interação no endereço público, não apenas pela existência de um commit.

## Reprodução e preservação

Na raiz do repositório, Python 3.12 e Node compatível com `node:test`:

```sh
pip install beautifulsoup4==4.15.0 playwright==1.63.0
python -m playwright install --with-deps chromium
python tools/sc_semantic_v2_ui/build.py
PRESERVATION_BASE=<sha-da-base-do-PR> python tools/sc_semantic_v2_ui/qa.py
```

O build valida IDs, pertença de fontes, elegibilidade e integridade das frases contra as entradas aprovadas. Produz os mesmos arquivos ao ser repetido. Não acessa a rede, não usa palavras-chave para atribuir pautas e não edita os arquivos de origem da auditoria.

O QA limita as mudanças no index aos blocos autorizados e compara os demais arquivos com a base efetiva do PR. Cabeçalhos, fotos, redes, trajetórias eleitorais, navbar, hero, rotação, rodapé e dados das outras frentes são protegidos. O runtime v1 usado como referência tem hash fixado; uma alteração nele exige revisão da adaptação, não integração silenciosa.

Os builders anteriores documentam etapas históricas e não devem ser usados como último passo de publicação da interface v2. Caso seja necessário reconstruir etapas anteriores, execute o build v2 por último e revise o diff antes de publicar.

## Testes e seus limites

A suíte Node compara todas as combinações de um, dois e três grupos em OR/AND, além do catálogo inteiro, com a auditoria independente do payload. Verifica também contagens, ausência de propagação entre famílias, exclusão das 11 associações reclassificadas, busca e preservação de ordem/inputs.

Os testes Chromium cobrem 320, 360, 390, 430, 768, 1024 e 1440 px, filtros, busca, resultado vazio, limpeza, remoção individual, foco, fechamento, mudança de breakpoint, links para fichas ocultas, referências, navbar e rotação diária. Também exercitam falhas de assets e JavaScript desativado. Fontes e imagens externas são bloqueadas nos testes; não é uma inspeção das fotos nem teste em aparelho físico ou leitor de tela real.

A preparação aprovada do run 35715431161 registrou 649 verificações, incluindo a execução dos nove testes Node, e zero falhas. Não são 658 verificações independentes. A revisão visual examinou as capturas de 320 px do painel, de 390 px dos blocos e de 1440 px dos filtros e fontes. O QA não certifica automaticamente interpretações políticas, a veracidade de resultados alegados pelas campanhas ou completude dos programas.

## Replicação posterior

Nenhuma outra edição recebe filtros nesta entrega. Para replicar, reutilizar o motor, a estrutura do painel e o contrato, fornecendo **matriz própria**, modelos editoriais aprovados, IDs de candidaturas e fontes correspondentes. Recalcular contagens e grupos com resultados e executar testes contra a base efetiva daquela frente.

Nunca copiar associações de uma candidatura ou partido para outra. Não preencher grupos vazios com inferências. A taxonomia continua expansível mediante revisão documental; esta implementação não torna as 29 famílias um inventário completo de todas as políticas públicas.

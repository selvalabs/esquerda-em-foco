# SC/Federais — leitura editorial e Selecionados

Issue #36, Round 2. A implementação usa os dados editoriais preparados no PR #37 e conserva o recorte documental de 21/09/2026. Este documento descreve a arquitetura; a confirmação da publicação fica em relatório separado.

## Leitura editorial

As 48 fichas são renderizadas estaticamente: 67 parágrafos dos 39 blocos documentados em 29 fichas, mais os avisos das 19 lacunas. Os títulos públicos são Pautas atuais, Outras posições, Atuação registrada e Fontes e contexto. Não houve nova pesquisa ou alteração de fontes, associações ou elegibilidade.

Cada parágrafo mantém os IDs dos itens e associações aprovados. A primeira referência de uma fonte em um bloco recebe um rótulo legível; repetições ficam compactas. Data de publicação desconhecida não é preenchida pela data de consulta. A informação detalhada continua em Fontes e contexto. As ressalvas essenciais são apresentadas próximas do texto, e todas as limitações originais permanecem disponíveis.

Os motivos dos filtros aparecem como indicações recolhidas **Neste trecho**, ligadas aos parágrafos por ID de associação. Ao abrir, o leitor encontra o registro específico e sua fonte. Não há associação por palavra-chave nem indicação de que todo o parágrafo corresponde a uma única pauta. O motor e o conjunto de 112 associações elegíveis da v2 permanecem intactos.

## Coleção de consulta individual

O controle Selecionar/Selecionado aparece em cada ficha. A navbar mostra um atalho e a contagem; quando há itens, uma barra discreta acima do rodapé oferece acesso à coleção. O conteúdo dessa barra não cobre o rodapé.

A coleção aceita todas as 48 fichas na ordem em que foram selecionadas. Não ordena por partido, votos, pautas, experiência ou quantidade de fontes. Não há comparação lado a lado, seções sincronizadas, diferenças calculadas ou recomendações. Anterior/Próxima percorrem uma ficha por vez.

A implementação move o próprio elemento da ficha para um diálogo nativo, deixando um marcador na posição original. Ao trocar ou fechar, devolve esse mesmo elemento ao marcador. Assim, não cria cópias dos dados, fotos, fontes ou IDs. Cabeçalhos, redes e trajetória eleitoral são os mesmos da listagem.

A busca e os macrofiltros mantêm estado independente da coleção. Uma ficha ocultada pelo filtro continua selecionada e pode ser aberta no leitor. Fechar o leitor restaura a ficha e reaplica os critérios existentes, preservando a ordem da listagem e a posição de rolagem de origem. Ir à ficha na lista utiliza o roteamento de âncoras existente, que informa quando precisa remover critérios para revelar o destino.

A coleção não é persistida. Uma visita nova sem fragmento começa vazia; um link de coleção reconstrói os IDs e a ordem. Não são usados cookies, localStorage, sessionStorage, analytics ou backend de favoritos. O contador de acessos continua desativado.

## Compartilhamento público

Uma ficha usa a âncora `#candidato-ID`. Uma coleção usa o contrato versionado:

```text
#selecionados=<ids>&v=1&edicao=sc-federais&ficha=<id>
```

O núcleo de seleção aprovado no Round 1 é copiado sem alteração. Valida edição, versão e IDs, remove duplicatas, limita entradas excessivas e não substitui uma coleção válida por um link inteiramente inválido. Os links mantêm o subdiretório do Pages ou a raiz do site quando servido na VPS. Parâmetros de rastreamento não são carregados para o link compartilhado.

O link guarda IDs e ordem, não uma cópia histórica dos textos. O destinatário verá o conteúdo disponível quando abrir o site. O fragmento não integra o alvo da requisição HTTP, mas isso não o torna secreto: o aplicativo e as pessoas que recebem o link podem ler os itens incluídos. A interface informa essa limitação.

O diálogo oferece Copiar link, WhatsApp e, quando suportado, Outros aplicativos pelo compartilhador nativo. O link do WhatsApp contém mensagem de consulta e URL, sem destinatário. A pessoa escolhe o contato e confirma o envio no aplicativo. O site não lê contatos nem envia mensagens automaticamente.

Cancelar o compartilhamento não dispara outro canal. A resolução da API nativa é descrita como entrega ao compartilhador, não confirmação de recebimento por contato. A cópia só anuncia sucesso após confirmação da API; caso falhe, o endereço permanece selecionável para cópia manual. Resultados assíncronos de um diálogo já fechado não alteram um novo diálogo.

## Layout e acessibilidade

Os diálogos têm posicionamento fixo e rolagem própria. A navegação às referências não deve deslocar o painel para fora da tela. O cabeçalho do leitor e o botão de retorno ficam acessíveis durante a rolagem. Fechamento por Escape e por clique externo, foco em diálogos aninhados e confirmação de limpeza são tratados.

A navbar mantém os links existentes e o menu hambúrguer no mobile. Entre 761 e 1100 px, os links ocupam uma segunda linha para evitar colisão com o novo atalho. No desktop mais largo o atalho inclui o texto Selecionados; em larguras menores, o ícone e o contador têm nome acessível equivalente.

Os botões mantêm área de toque apropriada, estado aria-pressed e foco visível. O gesto horizontal percorre a coleção sem impedir a rolagem vertical da página. Nenhum atributo de acessibilidade implica que tenha sido usado um leitor de tela real; os testes registram o alcance efetivo.

## Arquivos e reprodução

Entradas preservadas:

- `data/sc-editorial-selected-r1/editorial.json` e `paragraph-locations.json`;
- `data/sc-semantic-v2/` e `data/sc-semantic-v2-ui/payload.json`;
- catálogo de temas e runtime v2 usados como base;
- `tools/sc_editorial_selected/selection-core.cjs`.

Saídas da integração:

- `index.html`, apenas nas áreas editoriais, metodologia, índice textual e controles autorizados;
- `assets/editorial-selected.css`, `selecionados.js`;
- `assets/selecionados-core.js`, cópia do núcleo aprovado;
- `assets/pauta-filters-editorial.js`, adaptação de apresentação do motivo dos filtros;
- `data/sc-selected-ui/manifest.json`, `qa.json` e `extra-qa.json`.

Na raiz:

```sh
pip install beautifulsoup4==4.14.3 playwright==1.57.0
python -m playwright install --with-deps chromium
python tools/sc_selected_ui/build.py
PRESERVATION_BASE=<base-efetiva-do-PR> python tools/sc_selected_ui/qa.py
python tools/sc_selected_ui/extra_qa.py
```

A compilação não pesquisa a internet, não infere pautas e é determinística. Não usar os builders das etapas históricas como último passo de publicação: eles descrevem layouts anteriores. Reconstruir a integração atual por último e revisar o diff.

O workflow testa a preparação e o merge candidato contra o main efetivo. Somente saídas com ambos os relatórios aprovados são versionadas. Após o merge, a verificação pública compara os bytes de 12 arquivos por SHA-256 e abre o site com um navegador para testar a coleção em um novo contexto, simulando o destinatário do link.

## Limites dos testes e continuidade

A validação de vínculos não certifica automaticamente a interpretação política. A redação vem da revisão aprovada, e as evidências permanecem intactas. As lacunas não são eliminadas pelo fechamento desta issue.

Os testes usam Chromium em sete larguras. Compartilhamento nativo e clipboard são simulados para testar resultados, cancelamento e falhas. Os links do WhatsApp são conferidos, mas não há envio de mensagens ou teste em conta pessoal do usuário. Imagens e fontes externas são bloqueadas nos ensaios. Não se afirma teste em aparelhos físicos, leitor de tela real ou inspeção individual de todas as fotos.

As demais edições do projeto não receberam os controles. A estrutura pode ser replicada depois com catálogos, conteúdo e IDs próprios, sem copiar associações entre pessoas ou legendas. O site continua estático e não precisa de backend para a coleção ou para os filtros.

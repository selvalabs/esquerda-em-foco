# Contrato — leitura editorial e Selecionados

Issue #36 · Round 1 · 22/09/2026. Baseline: `d8bf0ae43a24f0f8f297316bb366e497dc3dfc8c`.

## Delimitação

A entrega prepara a redação pública e uma **coleção de fichas para consulta individual**. Não inclui comparação entre candidaturas, cards lado a lado ou seções sincronizadas. Essa delimitação substitui a parte comparativa da proposta inicial; seleção, remoção, leitura e compartilhamento permanecem.

A prévia é isolada, não é carregada pelo site e não será tratada como publicação de uma funcionalidade pronta. O Round 2 deve integrar os componentes e testar a produção. A issue permanece aberta.

## 1. Camada editorial

Os modelos em `data/sc-semantic-v2/` e o payload v2 publicado são entradas somente de leitura. Não modificar fatos, fontes, períodos, natureza ou elegibilidade para variar a redação.

A nova camada mantém os mesmos IDs de pessoa e seção, e associa cada parágrafo a um conjunto explícito de `item_ids`, `association_ids` e `source_ids`. Os 145 itens permanecem representados. A narrativa pode agrupar itens próximos; uma fonte não deve ser atribuída a uma frase que não sustenta.

Rótulos públicos: **Pautas atuais**, **Outras posições**, **Atuação registrada**, **Fontes e contexto**. “Atuação registrada” evita sugerir que iniciativas de 2026 pertencem necessariamente a outro mandato. A data do levantamento fica visível para não prometer verificação contínua.

As ressalvas que mudam o sentido ficam junto do texto: fonte indisponível, autoria atribuída a terceiro, data não confirmada e relato de voto não reconferido. Explicações de procedimento ficam em Fontes e contexto. Nenhuma limitação original é apagada.

Cada fonte recebe um rótulo legível de tipo e data original, quando confirmada. Data de consulta não preenche data de publicação. “Apresentação da candidatura · sem data original informada” é intencionalmente distinto de “Entrevista · set/2026”.

### Motivo dos filtros

`paragraph-locations.json` liga cada associação ao parágrafo relevante e conserva a frase de evidência exata. No Round 2, isso permitirá levar o leitor ao trecho em vez de repetir um mini-relatório. Não destacar todo um parágrafo como se suas diferentes afirmações fossem a mesma pauta. Nunca buscar palavras-chave para recriar associações.

Se a localização não permitir destacar uma frase com precisão, usar apenas um link curto para o trecho e manter a evidência específica acessível. A redução de duplicação não autoriza perder a direção da posição ou a fonte.

## 2. Estado de Selecionados

`selection-core.cjs` é um núcleo sem DOM, rede, cookies ou armazenamento. Expõe `createStore`, `parseFragment`, `collectionUrl`, `candidateUrl`, `shareData`, `whatsappUrl`, `nativeShare` e `copyLink`.

O estado é uma lista ordenada de IDs do catálogo atual, todos strings. Adicionar de novo não duplica. Remover não altera os demais. Reinserir coloca no fim. `snapshot()` devolve uma cópia, não uma referência mutável. Nenhum campo de voto, mandato, fonte ou pauta determina a ordem.

Não há limite artificial de três ou quatro fichas; as 48 desta edição podem ser selecionadas. A seleção não depende da busca nem dos filtros. Ao voltar à lista, preservar o texto de busca e, na futura integração, a seleção de pautas e a posição de leitura quando possível.

A coleção abre **uma ficha por vez**. Os controles Anterior e Próxima percorrem a ordem escolhida. As seções de uma ficha não são sincronizadas com outra. Remover a ficha aberta leva à próxima existente ou à anterior quando necessário. Coleção vazia tem mensagem própria, sem ficha residual.

A seleção existe somente em memória. Recarregar perde o estado, salvo quando um link contém os IDs para reconstruí-lo. A interação cotidiana não grava automaticamente os IDs na barra de endereço.

## 3. Formato de URL v1

Exemplo estrutural:

```text
#selecionados=<id1>,<id2>&v=1&edicao=sc-federais&ficha=<id-aberto>
```

A serialização usa `URLSearchParams`; vírgulas podem aparecer como `%2C`. O ID de `ficha` deve pertencer à coleção; caso contrário, abre-se a primeira ficha válida. Não incluir tema preferido, seção comparativa, filtros ou dados pessoais no link.

O parser tem lista permitida de IDs, versão e edição. Duplicatas são removidas mantendo a primeira ocorrência. IDs inexistentes são ignorados com aviso; quando nenhum é reconhecido, o estado existente não é substituído. Versão/edição desconhecida, parâmetros duplicados, codificação inválida e entradas acima de 4096 caracteres são recusados sem quebrar a página. O limite de segurança é suficiente para todas as 48 fichas e não deve ser usado para truncar silenciosamente a coleção.

Âncoras existentes como `#candidato-<id>` continuam representando uma ficha, não uma seleção. Outras âncoras pertencem ao roteamento já existente e não são interceptadas pelo núcleo da coleção.

O link reconstrói **IDs e ordem**, não uma cópia histórica do conteúdo. O texto e a situação documental poderão ter sido atualizados quando outra pessoa abrir a página. IDs ausentes em uma edição futura não devem ser substituídos por candidatos supostamente equivalentes.

O construtor recebe uma base configurada pelo site, preserva o subdiretório do GitHub Pages ou a raiz da VPS e remove parâmetros de rastreamento e fragmentos antigos. Não aceitar protocolos executáveis ou URLs com credenciais.

## 4. Privacidade do fragmento

O fragmento identifica estado no cliente e não integra o alvo de uma requisição HTTP. Isso não torna o link secreto: o navegador, extensões, scripts da página, aplicativos e pessoas que recebem o link podem lê-lo. Ao escolher WhatsApp, o link completo será parte da mensagem preparada para aquele aplicativo. Não afirmar anonimato, criptografia própria ou ausência de acesso de terceiros ao conteúdo compartilhado.

Não enviar IDs de selecionados ou pautas ao contador. Não usar encurtador, backend de favoritos, analytics, cookies, localStorage ou sessionStorage. Não registrar o fragmento em logs de erro. A seleção compartilhada pode revelar uma escolha de consulta; a página deve explicar que qualquer pessoa com o link pode abrir a coleção.

Referências: [RFC 9110, URI e identificador de destino](https://www.rfc-editor.org/rfc/rfc9110.html#section-7.1) e [WHATWG URL Standard](https://url.spec.whatwg.org/). Esses padrões definem o comportamento técnico; as restrições adicionais acima são decisões deste projeto.

## 5. Compartilhamento

Uma ficha usa a âncora já publicada e uma frase de consulta, sem recomendação. Uma coleção usa mensagem genérica: “Fichas reunidas para consulta no Esquerda em Foco.” O nome da coleção não indica intenção de voto.

O compartilhamento nativo só é chamado após o acionamento da pessoa. Falta de suporte leva às alternativas visíveis, não a envio automático. Cancelamento não dispara WhatsApp nem copia para a área de transferência. A resolução da promessa indica entrega ao compartilhador, não confirmação de entrega a um contato.

Referência: [W3C Web Share API](https://www.w3.org/TR/web-share/), especialmente ativação do usuário, escolha de destino e tratamento de cancelamento.

A ação WhatsApp usa:

```text
https://wa.me/?text=<mensagem-e-link-codificados>
```

Não definir um destinatário, importar contatos nem pedir telefone. A pessoa escolhe o contato e confirma o envio no aplicativo. O texto é codificado uma vez; acentos, espaços e o fragmento devem ser preservados.

Referência: [Central de Ajuda do WhatsApp — clique para conversa](https://faq.whatsapp.com/5913398998672934/?locale=pt_BR). O exemplo sem número prepara a mensagem e permite escolher destinatário. Disponibilidade no aparelho precisa de teste real no Round 2.

“Copiar link” só anuncia sucesso quando a API confirma. Em caso de falha ou falta de suporte, exibir o endereço num campo selecionável. Não usar sucesso fictício, permissões persistentes ou tentativas ocultas de outros canais.

## 6. Proteção da prévia

O protótipo permite testar links locais de coleção sob HTTP. Esses links **não são apresentados como links funcionais do site público**. Compartilhamento externo de coleção fica desativado até a integração. A prévia informa essa limitação ao abrir o diálogo.

Uma ficha individual pode ter seu link publicado preparado pelo protótipo, porque a âncora correspondente já existe. Os testes não enviam esse link a contatos; conferem o endereço e simulam Web Share/clipboard. No arquivo HTML aberto sem servidor local, a seleção e a leitura funcionam, mas o teste de link de coleção exige HTTP.

## 7. Integração seguinte

O Round 2 deve ligar os botões aos cards reais, manter a busca e os macrofiltros independentes da coleção, reconciliar o namespace do fragmento com o roteador existente e preservar navbar, rodapé, rotação e dados eleitorais. Manter só uma fonte de estado e evitar IDs duplicados ao abrir uma ficha.

Antes de publicar: testes de 0, 1, 2 e 48 selecionados; remoção da ficha aberta; ida/volta; versão/IDs inválidos; teclado/foco/fechamento; ausência de overflow em 320–1440 px; links com subdiretório e raiz; privacidade; contingência sem JavaScript e sem API de compartilhamento. Confirmar os arquivos servidos e testar os aplicativos disponíveis sem afirmar ensaio em dispositivo que não foi utilizado.

As outras frentes permanecem fora do escopo. A infraestrutura pode ser reutilizada posteriormente, mas os textos, IDs, fontes e associações exigem a base própria de cada edição.

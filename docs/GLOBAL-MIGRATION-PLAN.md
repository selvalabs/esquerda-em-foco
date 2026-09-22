# GLOBAL-04 · migração funcional por lotes

Issue #43; epic #39. Migração funcional incremental. Cada lote renova a baseline no `main` efetivamente publicado e não restaura snapshots antigos.

## Lote 01 · coleção comum e navegação profunda

Executar G4-A, G4-B, G4-E e a parte de G4-F/G4-G necessária à liberação:

1. Inventariar as seis edições publicadas e registrar capacidades, baseline e pendências por edição.
2. Reproduzir a falha SP (busca oculta uma ficha, hash aponta a ela e ela permanece invisível). Corrigir com aviso, retorno aos filtros anteriores e testes de hashchange, recarga e histórico.
3. Integrar o núcleo GLOBAL-02 à coleção das seis edições. Preservar a ordem de seleção, uma ficha original por vez, fontes, seleção/remover/limpar, retorno à lista e ausência de IDs duplicados.
4. Oferecer compartilhamento individual e da coleção por link, WhatsApp e Web Share com fallback. Preservar links SC v1 e emitir links v2 identificando eleição/UF/cargo; não acessar contatos, armazenar preferências nem enviar mensagens.
5. Preservar controles e semânticas dos filtros existentes. Não reclassificar temas históricos como apoios atuais para conseguir paridade visual.
6. Reaplicar a camada funcional depois do refresh de um renderer legado, sem sobrescrever home, aliases ou dados.
7. Executar QA de coleção com as 249 fichas SP e catálogo sintético acima de 256, foco/teclado/URLs/fontes, filtros/ordenação, preservação de dados e comparação do publicado.

Este lote não encerra a #43: G4-C (consulta comum e multisseleção onde ausente) e G4-D (composição editorial/transparência/evidência e revisão explícita de equivalências) continuam em lotes seguintes. Os filtros específicos já funcionais são preservados, não declarados novamente como migração concluída.

## Edições

SC Federal 48; SC Estadual 97; RS Federal 111; PR Federal 115; PR Estadual 140; SP Federal 249. Estas são contagens esperadas da baseline, a conferir no código; não projeções nem contagem de candidaturas aptas. A soma de fichas publicadas é 760. RS Estadual permanece somente em branch; SP Estadual não é inventada.

## Contratos e preservação

A coleção pertence à edição e ao ano, usa IDs reais e ordem de inserção. Mantém a ficha original, sem duplicar o documento nem dar pontuação/recomendação. Limite defensivo de transporte é explícito; excesso não corta a seleção. Cancelar o compartilhamento não dispara outro canal. Sucesso de clipboard só é anunciado depois da confirmação da API.

Nenhuma coleta TSE, síntese política, fonte, data cadastral, associação temática ou dado de pesquisa pode ser alterado neste lote. A evidência original e as limitações acompanham a ficha no leitor. Filtros permanecem ativos ao voltar à lista.

O refresh não autoriza reconstruir pesquisa a partir de snapshots antigos. Baselines congeladas são prova de preservação, não dados atuais para repor no main. Issues editoriais e liberação de RS Estadual permanecem independentes.

## Gates de conclusão do lote

Baseline reproduzida, teste pré-correção documentado, arquivos de pesquisa preservados, UI exercitada em desktop/mobile e sem JavaScript, navegação/fonte/coleção reabertas em contexto novo, outputs determinísticos, CI somente leitura na liberação, PR revisado e versão publicada conferida. A abertura do PR ou execução verde de uma suíte parcial não conclui o lote nem a #43.

Referências técnicas: HTMLDialogElement e eventos de fechamento/foco, MDN: https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement ; diálogos nativos: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog .

## Lote 02 · consulta comum e filtros compartilháveis

Baseline: `1a71c03987f52104af12af42eebda52449ff5570`, depois da publicação do lote 01.

Executar G4-C sem reclassificar conteúdo: multisseleção de partidos em OR nas seis edições, busca e critérios locais representados por um contrato comum, estado novo em memória e compartilhamento explícito por fragmento versionado. PR/SP continuam aceitando seus dialetos antigos, mas novas interações não mantêm escolhas automaticamente na querystring.

A semântica temática permanece local e explícita: SC Federal = `current_support`; SP Federal = `documented_topic`; PR Federal/Estadual = `legacy_context` em AND. SC Estadual e RS Federal não recebem tema inventado apenas para obter paridade. Critérios cadastrais, de mandato, histórico ou localidade só aparecem onde a edição já possui campos e controles adequados.

O lote deve manter Selecionados/compartilhamento do lote 01, filtros e fontes próprios, 760 fichas e a home/hubs. O refresh dos renderers precisa reaplicar a camada de consulta depois da coleção. A liberação exige testes em dois mounts, 320–1440 px, importação legada, link explícito em navegador novo, critérios inválidos/estrangeiros atômicos, fallback noJS, rebuild e conferência pública.

G4-D continua depois deste lote: composição editorial, evidências, transparência e crosswalk taxonômico revisado. A issue #50 de caderno multi-edição não entra no caminho crítico.

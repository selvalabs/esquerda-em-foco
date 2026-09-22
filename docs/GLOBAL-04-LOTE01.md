# GLOBAL-04 · lote 01 — Selecionados e navegação profunda

Parte da issue #43 e do epic #39. Implementação no PR #49.
Baseline: `22bf032f12b44ec3471f90736035c3e020deea6d`.

## Entrega funcional

O leitor de SC foi adaptado para as seis edições publicadas, usando o núcleo
parametrizado GLOBAL-02. A interface permite selecionar fichas, abri-las uma de
cada vez, avançar/recuar na ordem da seleção, remover itens, confirmar a limpeza e
compartilhar ficha ou conjunto. A entrada fica junto à busca; após escolher uma
ficha, uma barra de acesso também acompanha a consulta.

Cada edição mantém seus textos, fontes, cadastro, filtros e regras de ordenação.
A coleção não é ranking, lista recomendada ou comparação por pontuação. A mesma
ficha original é movida temporariamente para o leitor, deixando um marcador na
posição da lista. Ao fechar, retorna ao lugar. Não há clones com IDs duplicados.

As edições são separadas por eleição, UF e cargo. Mudar de edição ou recarregar
uma página sem link de coleção não transfere escolhas automaticamente. Para guardar
ou encaminhar o conjunto, a pessoa usa o link explícito. Não há persistência de
escolhas em localStorage, sessão, cookies, backend ou analytics neste recurso.

## Compartilhamento

O novo link usa o fragmento versionado `eef=collection&v=2`, incluindo a identidade
da edição, os IDs na ordem da escolha e a ficha aberta. Os links SC v1 continuam
aceitos, inclusive quando chegaram à raiz anterior à home. Novos links usam a
rota canônica da edição. Um link individual contém só sua âncora; não carrega a
busca nem as demais escolhas de quem o criou.

WhatsApp recebe texto e URL preparados, sem destinatário previamente escolhido.
Nada é enviado automaticamente. O compartilhador nativo pode ser cancelado, sem
cópia ou envio por outro canal. A mensagem de cópia bem-sucedida só aparece depois
de confirmação da API; quando indisponível, o campo recebe foco para cópia manual.

O link é compartilhável, não secreto, e identifica registros na edição atual;
não é uma cópia congelada da ficha. A seleção não tem limite artificial de 48 ou
256 itens. O tamanho defensivo de transporte é o definido no núcleo GLOBAL-02;
excedê-lo resulta em aviso, sem retirar itens silenciosamente da coleção.

## Correção de links SP

A falha identificada na GLOBAL-01 consistia numa ficha escondida pela busca
continuar invisível quando seu hash era aberto. O runtime SP agora suspende os
critérios que impedem a leitura, explica a mudança e oferece “Restaurar minha
consulta”. A restauração recoloca os filtros e remove a âncora que impediria sua
aplicação. Histórico do navegador e links recebidos já com query/âncora têm testes
próprios. Âncoras desconhecidas não limpam a consulta.

O estado de consulta é separado da coleção. Abrir e fechar o leitor normalmente
não limpa filtros; a ação explícita de ir à ficha na lista é tratada pela
navegação profunda de cada edição. A recuperação SP não cria novas associações
políticas ou converte atuação histórica em apoio atual.

## Arquitetura e manutenção

- `assets/global/selection-adapter.js`: ponte entre catálogo/edição e núcleo puro.
- `assets/global/selection.js`: leitor, foco, confirmação e ações de compartilhamento.
- `assets/global/selection.css`: adaptação visual do leitor e fallback progressivo.
- `templates/global04/collection.html.txt`: markup do leitor, sem cadastro eleitoral.
- `tools/global04/build.py`: aplicar/reaplicar a camada na edição atual.
- `tools/global04/prepare.py`: geração de desenvolvimento a partir das referências revisadas.
- `tools/global04/patch_runtime.py`: mudanças explícitas nos pontos de integração.

O refresh da GLOBAL-03 chama o build funcional apenas para edições que ativaram
`global_collection_v2`. A reconstrução de uma edição não deve sobrescrever a home,
repor a navegação antiga ou perder o leitor. O bootstrap GLOBAL-02 não é usado
contra a home atual. As referências congeladas não autorizam restaurar pesquisas
antigas por cima de conteúdo novo.

## Validação e limites

A liberação exige testes de lógica; preservação por arquivo e por conteúdo de
ficha; reprodução prévia da falha SP; navegador em dois mounts e sete larguras;
249 fichas reais SP por link; catálogo sintético de 513 registros em rota exclusiva
de teste; fontes, foco, cancelamento/cópia e funcionamento sem JavaScript. Os
resultados e SHAs efetivamente executados são registrados no PR e no relatório de
QA do lote. Um workflow iniciado não equivale a uma aprovação.

Os testes controlam o resultado das APIs de clipboard e compartilhamento nativo
para exercitar cancelamento, sucesso e erro. Isso não é envio real pelo sistema
operacional ou WhatsApp. As requisições externas são bloqueadas nas suítes do lote;
a validação não certifica a disponibilidade atual de todas as fontes políticas.
Não foram feitos nova coleta eleitoral, teste em aparelho físico ou certificação
integral de acessibilidade com leitor de tela.

## O que permanece na #43

G4-C: compor a consulta comum, aproveitando multisseleção partidária de SP,
combinações de PR e explicabilidade de SC. G4-D: adequar estrutura editorial,
evidências e transparência com os avanços de SC Estadual, RS, PR e SP. Os formatos
de tema documentado, apoio atual e contexto legado continuam distintos. O
crosswalk de taxonomias requer revisão explícita, não conversão por palavra-chave.

O arquivo `data/global-integration/migration-status.json` registra antes/depois e
pendências de cada edição. A navegação global já veio da #42. RS/Estaduais mantém
sua pesquisa e liberação independentes. Este lote não encerra a #43 nem o epic.

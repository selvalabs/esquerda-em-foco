# Selecionados — validação anterior à publicação

Issue #36, Round 2. PR de integração #38. Este registro documenta a preparação; não afirma que a versão já foi publicada.

## Preparação aprovada

Run: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35732576691

Código testado: `3275c2225fc047423acb0a2bb1e874802dd593dd`.
Saídas validadas: `94091d3e6565f722f47a15707ef63d8fe0fb39f5`.
Base: `d8bf0ae43a24f0f8f297316bb366e497dc3dfc8c`.

O relatório principal aprovou **580 verificações**, sem falhas. O relatório adicional aprovou **118 verificações**, sem falhas. Os 12 testes Node do núcleo de seleção e compartilhamento estão incluídos no relatório principal; não são somados novamente.

Foram preservados byte a byte **1.603 arquivos preexistentes fora das áreas autorizadas**. As verificações adicionais do index protegeram as identidades, os cabeçalhos, redes, trajetórias e âncoras das 48 fichas, além dos 67 parágrafos exatos da redação aprovada, fontes e limitações. As associações e o payload semântico v2 não foram alterados.

## Casos de integração

Chromium em 320, 360, 390, 430, 768, 1024 e 1440 px. Seleção de todas as 48 fichas, navegação individual, remoção da ficha aberta, limpeza confirmada, retorno à listagem e reconstrução do conjunto por link foram exercitados. A busca e os filtros OR/AND mantêm sua independência da coleção.

Foram verificados a ausência de IDs duplicados, os links antigos, a abertura de fontes dentro do leitor, o acesso à ficha na lista quando ocultada por filtros, o estado vazio, a rotação diária e a posição da barra de seleção acima do rodapé. Falhas dos assets mantêm o conteúdo e os recursos independentes; sem JavaScript, os textos continuam no HTML.

Os testes do compartilhamento verificaram o link, codificação para WhatsApp, cancelamento, entrega ao compartilhador e cópia manual. Web Share e clipboard foram simulados. Nenhuma mensagem foi enviada, nenhum contato foi acessado e nenhum recebimento em aplicativo externo foi afirmado.

## Revisão visual e correções

As capturas finais do painel individual em 320, 390 e 1440 px e da navbar em 768 px foram inspecionadas. O layout intermediário de tablet foi reorganizado em duas linhas para evitar sobreposição do atalho de Selecionados com os links existentes.

Foi corrigido o posicionamento dos diálogos para que a navegação às fontes não os desloque para fora do viewport. O cabeçalho e o retorno à lista continuam acessíveis. A regressão verifica as coordenadas do painel e a possibilidade de atingir o botão, não apenas sua presença no DOM.

Uma tentativa de regressão de rolagem confundia a rolagem programática de `Locator.click()` com a posição anterior ao clique da pessoa. A verificação passou a usar o centro visível e testado da navbar por coordenadas de ponteiro; mantém a exigência de restaurar a posição original, com tolerância de dois pixels. O comportamento da aplicação não foi alterado para acomodar uma expectativa incorreta do teste.

A primeira execução de integração também encontrou uma falha no próprio gravador do relatório (importação ausente de `dump`) e problemas de layout. Foi corrigida antes da preparação aprovada. Tentativas que falharam não foram publicadas nem contadas como aprovações.

## Artefato e limites

Artifact: **10696745576**, `sc-selected-ui-prepare`.
SHA-256 do ZIP: `5f2f2a5c7f54dc3ab6e4b068ec9e81121530029f01412e267c5814bf70f72514`.

As capturas e os testes bloquearam imagens externas. Não equivalem a inspeção de todas as fotografias, aparelho físico ou leitor de tela real. A conferência de vínculos e de reprodução não é certificação automática de interpretações políticas.

Antes do merge, o PR repete as duas suites contra o main efetivo. Depois do merge, o workflow público deve conferir 12 arquivos por HTTP/SHA-256 e abrir o link da coleção em um novo contexto de navegador. A issue #36 só deve ser encerrada após essa prova. A comparação entre candidaturas, cards lado a lado e seções sincronizadas não faz parte da entrega.

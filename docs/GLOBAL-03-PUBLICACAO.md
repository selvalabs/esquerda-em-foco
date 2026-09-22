# GLOBAL-03 · publicação da home geral

Data: 22/09/2026. Issue #42, implementação no PR #47.

## Versão publicada e conferida

Merge de publicação: `0827e49ad8e001a4345313ec95e785792daaa798`.
Head validado: `2af97f240e5bebc3d0504cc8b2c6c612fa77f99d`.
Baseline: `4d6ea9847f59fc6dfd52d57601b0ab19c8d3ecab`.
O head, o merge candidato e o merge efetivo têm os mesmos arquivos.

Site: https://selvalabs.github.io/esquerda-em-foco/

Run público: https://github.com/selvalabs/esquerda-em-foco/actions/runs/35762102798 — sucesso.
Artefato: `10710516417`, SHA-256
`f62c57791d53dcffa7bb6c02b6cae6d4f57f5a3810dd3167ae2069d3ab5826ae`.

A conferência HTTP, registrada em `2026-09-22T17:40:07.522325+00:00`, validou os
**41 arquivos críticos**, com status 200 e SHA-256 igual ao commit. A resposta a
um caminho inexistente aninhado retornou HTTP 404 e os bytes da página 404 esperada.
A suíte pública também aprovou **123 verificações de navegador** em 390/1440:
home, hubs, edições, menus, busca/limpeza, navegação, links antigos, coleção SC v1,
compartilhamento na rota canônica e reconstrução em contexto novo. Não houve envio
de mensagem por WhatsApp. As fotos externas foram bloqueadas nessa suíte.

A validação pré-publicação é documentada separadamente em
`GLOBAL-03-VALIDACAO.md`: 34 testes de contratos, 47 preexistentes, 2.288 checks de
preservação/navegador e 18 de rebuild. A maioria dos checks estáticos é preservação
de arquivos, não funcionalidades distintas. Reexecuções não são somadas.

## Compatibilidade dos verificadores legados

Após o merge, o workflow SP também foi disparado. Seus 273 checks de arquivos
públicos passaram, mas a navegação final ainda procurava 48 fichas de SC na raiz.
A raiz agora é a home geral. O run `35762102746` falhou nessa asserção, e o passo
seguinte de SC não foi executado. A falha não foi tratada como sucesso nem apagada.

O ajuste posterior fica restrito aos verificadores e à documentação; os HTML,
assets de produção e dados permanecem idênticos à versão acima. O verificador SP
passa a percorrer home → hub SC → edição SC → edição SP, preservando a exigência
original de 48 fichas/13 filtros em SC e as verificações SP de partidos, temas,
busca, evidências e 249 retratos locais. O verificador SC usa a rota e o arquivo
canônicos indicados pelo catálogo. Nenhuma asserção substantiva é relaxada.

Resultados e commits dessa compatibilidade são registrados no PR correspondente
e na issue #42 após execução. Este documento confirma o run público GLOBAL-03,
não antecipa a conclusão das suítes legadas ajustadas.

## Escopo preservado

A home e os quatro hubs estão publicados. As seis edições compartilham navegação
e mantêm seus dados e diferenças de recursos. RS/Estaduais continua não publicado;
SP/Estaduais não é criado artificialmente. As 760 fichas públicas e fontes foram
preservadas, sem nova coleta eleitoral ou pesquisa política.

#43 continua responsável por levar os demais recursos canônicos às edições,
inclusive o problema SP de ficha ocultada pela busca ao mudar a âncora. #44 fecha
a auditoria global. Não houve aparelho físico, leitor de tela real ou certificação
integral de acessibilidade. A integração de navegação não encerra a pesquisa.

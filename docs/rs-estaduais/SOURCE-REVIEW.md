# Revisão de fontes — RS / estaduais

Data de corte: **21 de setembro de 2026**. As fontes editoriais individuais, datas e localizadores acompanham `data/rs-estaduais/editorial.json`. Para páginas renderizadas em navegador, `rendered_body_sha256` identifica o corpo lido; não é apresentado como hash de um arquivo HTML original.

## Separações mantidas

Um registro eleitoral não confirma exercício de mandato. Um resultado anterior não confirma mandato atual. Uma página do próprio candidato sustenta uma declaração atribuída, não uma verificação independente de seus resultados. Uma proposição não é chamada de lei aprovada sem comprovação institucional. Uma votação nominal descreve um ato datado e não basta para concluir um posicionamento geral.

Os cinco mandatos de Porto Alegre foram conferidos na relação institucional em exercício e nos perfis correspondentes, com coincidência do nome civil e sem utilizar a seção de licenciados. Os votos nominais da ALRS incluídos nesta edição são datados de 25/08/2026; não foram utilizados como prova de exercício atual em 21/09/2026.

## Conteúdo que não foi transformado em pauta

| Candidatura / fonte | Achado da consulta | Tratamento |
|---|---|---|
| Regina Becker Fortunati — `reginabecker.com.br` | Página padrão de instalação WordPress, sem programa identificado. | Não foi criada síntese de pautas a partir desse conteúdo. |
| Gerson Burmann — `gersonburmann.com.br` | Apresentação com instruções de preenchimento e espaço reservado para imagem institucional. | Texto provisório não foi tratado como posicionamento confirmado. |
| Luciano Orsi — `lucianoorsi.com.br/pages/compromissos.html` | Seção de compromissos com conteúdo reservado para futura publicação. | Biografia atribuída registrada; pautas permanecem pendentes. |
| Ràquel Möller — `raquelmoller.com.br` | Prioridades temáticas explícitas, mas propostas detalhadas anunciadas para publicação posterior. | A síntese informa apenas as prioridades e explicita a falta de detalhamento. |
| Matheus Vicente — `matheusvicente.com.br` | Ferramenta de moldura de perfil, sem proposições recuperadas. | Não se inferiram pautas a partir de material de divulgação. |
| Maneco Hassen — `manecohassen.com.br` | Identificação eleitoral, sem texto programático recuperado. | Mantida a ficha eleitoral, com lacuna temática. |
| Andressa Mais Participação — `participacao.org` | Identificação e canais de contato, sem programa recuperado. | Não foram publicados contatos privados nem inferidas pautas. |
| Humberto Matos — `humbertomatos.com.br` | Apresentação e chamada para projeto regional; opções de resposta em formulário destinado a visitantes. | As opções do formulário não foram automaticamente atribuídas à candidatura. Documento completo ainda requer leitura. |
| Dr. Thiago — `clippingdrthiagoduarte.wordpress.com` | Publicações históricas de 2021–2022 e página de recortes. | Não foram apresentadas como propostas estaduais de 2026. |
| Gabi Rosa — `gabipsol.com.br/GABI/` | Posições explícitas, mas texto ainda redigido como pré-candidatura. | Posições atribuídas ao texto; registro e situação de 2026 vêm exclusivamente do TSE. Idade e dados pessoais de contato não reproduzidos. |

Uma notícia de Pepe Vargas sobre transição ecológica exibia **09/10/2026**, data posterior ao corte, em `https://pepevargas.com.br/artigo-pepe-vargas-transicao-ecologica-e-uma-escolha-de-futuro-para-o-rio-grande-do-sul/`. Ela foi excluída das sínteses desta edição até que a data seja esclarecida. As posições incluídas na ficha provêm de outras publicações anteriores ao corte.

## Limites de acesso e de cobertura

A consulta automatizada ao diretório da Assembleia Legislativa do RS teve timeouts, registrados em `institutional-discovery.json`. A consulta pelo navegador web não forneceu uma relação nominal utilizável para reconciliação integral. Por isso, não se afirmou uma quantidade completa de deputados estaduais atualmente em exercício dentro do recorte.

O rastreamento dos endereços declarados no TSE examinou todos os registros e não exigiu login em redes sociais. Endereço válido e página legível não significam revisão editorial concluída. Endereços malformados não foram corrigidos por adivinhação. Os totais de entradas inválidas no relatório referem-se a entradas das fontes, não necessariamente a pessoas distintas.

A revisão em navegador de páginas públicas gerou trechos temporários apenas para análise. Esses trechos não integram o site nem o pacote de entrega. O repositório conserva sínteses autorais, referências, localizadores e hashes, e não reproduções extensas dos textos das campanhas.

## Continuidade auditável

`candidate-coverage.csv` e `candidate-coverage.json` identificam cada candidatura e suas lacunas. Os próximos passos devem completar as fontes em falta, validar mandatos atuais nos diretórios institucionais, ampliar atos legislativos e conferir os votos históricos restantes. Nenhum campo ausente equivale à conclusão de que a pessoa não tem pauta, experiência ou atuação.


## Fechamento de recuperação — 22/09/2026

O relatório atual é `ad2-close/ENTREGA-A-D2.md`. Foram reproduzidas 61 sínteses, não 71, e 395 linhas com votos, não 394. Todos os 149 registros têm estado explícito da pesquisa. E/F e lacunas temáticas permanecem abertos. O cadastro eleitoral não foi atualizado por este fechamento.

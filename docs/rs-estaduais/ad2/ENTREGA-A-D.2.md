# RS / Deputados estaduais 2026 — A–D.2

**Pesquisa incremental executada; fechamento editorial integral ainda pendente.**

## Base e recorte

A correção canônica anterior a esta execução acrescentou duas candidaturas da REDE e duas do PSTU: a base recebida tinha 149 candidaturas, 50 sínteses e 99 lacunas. A–D.2 preserva essa correção; não atribui os quatro novos registros a esta pesquisa nem remove siglas do recorte.

## Resultado comparado

| Cobertura documental | Antes de A–D.2 | Depois |
|---|---:|---:|
| Candidaturas | 149 | 149 |
| Sínteses individuais de temas | 50 | 61 |
| Fichas sem síntese temática | 99 | 88 |
| Mandatos atuais confirmados | 15 | 16 |
| Fichas com atos institucionais | 26 | 31 |
| Linhas históricas com votos conferidos | 392 | 395 |

A tabela mede cobertura documental, não qualidade ou preferência política. Os grupos se sobrepõem.

## A — pesquisa individual

Foi registrada busca nominal para as 99 lacunas iniciais, com 118 consultas preservadas. 11 novas sínteses foram apoiadas por fontes individuais. As demais 88 lacunas exigem aprofundamento; uma busca ou um link indisponível não demonstram ausência de propostas.

O registro distingue apresentações individuais, entrevistas, opiniões assinadas, atos municipais e declarações históricas. Textos de 2025 ou anteriores são identificados como históricos, não como programa completo de 2026. A entrevista de setembro de Cleonice Back complementa a insuficiência antes registrada no site de campanha.

## B e C — mandatos e atos

Foi acrescentada a confirmação de Bruno Berté como vereador de Carazinho na relação institucional Atual Legislatura. A presidência mencionada em entrevista de 2025 não foi transferida para o presente. As doze chamadas aos sistemas municipais de São Jerônimo, Esteio e Jaguari retornaram timeout; nenhuma confirmação foi fabricada.

Foram acrescentados registros de proposta, aprovação legislativa, autoria de documento de comissão, reunião e posses históricas. A autoria de certidão não vira voto individual; anúncio de recurso não vira entrega; a aprovação legislativa não é descrita como implantação; a posse de suplente no passado não prova exercício atual.

## D — totais e registros antigos

Foram incorporados 3 totais: duas disputas anteriores de Rogério Chimanski e a disputa presidencial de Luciana Genro em 2014, esta em fonte nacional BR. Agora há 395 totais conferidos em 432 linhas históricas. Restam 11 totais sem confirmação e 26 posições de vice/suplência sem voto nominal próprio.

As 14 fichas históricas do DivulgaCand foram relidas com ID, ano, cargo e nome conciliados. Sua situação foi anotada exclusivamente no histórico; não substitui a situação de 2026. Renúncia ou indeferimento histórico não foi usado para inventar um zero nominal. Os arquivos por município/zona têm CRC e SHA-256 de seus membros; não se declara hash integral de arquivo nacional acessado por intervalos.

## Regressão e isolamento

Resultado: passed. Testes unitários: 67; verificações Chromium: 47. A verificação cobre dados, preservação de fontes, contexto eleitoral, repetição das etapas, controles de histórico e responsividade. E/F seguem pendentes.

Mudanças restritas à edição RS/estaduais, testes, documentação e workflows próprios. Não foram feitos merge, publicação, nova coleta eleitoral completa ou alterações às outras frentes. A configuração canônica compartilhada foi apenas lida.

## Arquivos

- `candidate-coverage.csv` e `.json`: as 149 candidaturas e o estado efetivo da pesquisa.
- `historical-vote-pendencies.csv` e `.json`: cada nulo com contexto e distinção entre pendência e cargo sem voto nominal próprio.
- `report.json`: métricas desta execução e limitações.
- `data/rs-estaduais/ad2-*.json`: consultas, fontes aceitas, fontes insuficientes e evidências eleitorais.
- `rs/deputados-estaduais/pesquisa.json`: consulta pública ao registro de pesquisa.

## Próximo requisito de fechamento

Aprofundar as fontes das fichas ainda sem síntese, ampliar confirmações institucionais e concluir E/F sobre a versão consolidada. Não é necessário inventar um programa para cada pessoa; é necessário documentar pesquisa suficiente e distinguir com clareza o que foi verificado do que permanece desconhecido.

# RS-FED-03 — fechamento editorial dos Deputados Federais do RS

## Estado de partida

Baseline do round: `1d38f52a2981091c0ce0fa46b64a98ac53e8c3cf`.

Branch preparada: `feat/rs-federais-fechamento-editorial`.

A revisão anterior deixou 107 fichas no recorte. Para este round, o conjunto operacional é de **63 fichas**: 61 sem síntese documental suficiente e duas com conteúdo apenas de trajetória, ainda sem síntese de pautas/atuação. Há também **8 registros históricos de votação nominal** ainda não reconciliados.

Distribuição dos 63 alvos:
- PCdoB: 1
- PDT: 20
- PSB: 17
- PSOL: 12
- PT: 11
- PV: 2

O manifesto executável do round está em `data/rs/rs-fed-03-targets.json`.

## Objetivo

Levar a frente federal do RS ao maior nível documental possível, pesquisando individualmente as 63 fichas remanescentes e tentando resolver as oito lacunas de votação, sem preencher qualquer campo por inferência.

O trabalho deve priorizar **qualidade e rastreabilidade**, não forçar 100% de preenchimento. Se, após pesquisa suficiente, determinada informação continuar sem fonte adequada, a lacuna deve permanecer explícita e nominalmente documentada.

## Escopo de execução

### A. Rebaseline e controle de concorrência

1. Antes de editar, comparar a branch com o `main` atual.
2. Registrar o novo HEAD se houver mudanças concorrentes.
3. Revalidar que as 63 fichas-alvo continuam sendo as mesmas ou documentar qualquer mudança oficial.
4. Não sobrescrever trabalho de SC, deputados estaduais, SP ou outras frentes.
5. Toda alteração compartilhada deve ser mínima, necessária e auditável.

### B. Pesquisa individual das 63 fichas

Para cada candidatura, executar pesquisa própria, preservando o ID TSE como chave estável.

Ordem preferencial de fontes:
1. TSE / Justiça Eleitoral;
2. Câmara dos Deputados, ALRS, câmaras municipais e outros órgãos públicos;
3. portais de transparência ou diretórios institucionais;
4. site individual da candidatura;
5. página individual do partido/federação;
6. redes oficiais;
7. entrevistas originais;
8. imprensa confiável apenas quando necessária para complementar fatos não disponíveis em fonte primária.

Para cada ficha, registrar no log:
- consultas realizadas;
- URLs consultadas;
- data da consulta;
- fonte aceita ou rejeitada;
- tipo da evidência;
- limitações;
- resultado editorial.

### C. Regra de síntese

Uma ficha só passa de pendente para documentada quando houver conteúdo individual específico e fontes suficientes.

Distinguir explicitamente:
- proposta de campanha de 2026;
- declaração pública;
- atuação legislativa;
- atuação em gestão pública;
- trajetória profissional/política;
- fato histórico;
- medida efetivamente executada.

Não:
- atribuir programa partidário automaticamente à pessoa;
- transformar menção a um tema em defesa de uma pauta;
- apresentar reivindicação como realização;
- transportar posição antiga para 2026 sem marcar o período;
- preencher texto genérico apenas para remover uma lacuna.

As duas fichas hoje classificadas como `trajectory_only` só serão consideradas fechadas em pautas/atuação se surgir evidência adicional adequada.

### D. Temas documentais

Manter o vocabulário controlado existente.

Só associar um tema quando houver fonte individual correspondente. Cada associação deve continuar apontando para uma ou mais fontes da própria ficha.

Não criar filtros visuais novos neste round. O trabalho é de conteúdo e dados; evolução de UI deve ser outra tarefa.

### E. Cargos atuais

Ampliar a auditoria de cargos eletivos atuais, priorizando as 63 fichas-alvo e casos em que o histórico sugira possível exercício atual.

Confirmação exige fonte institucional atual e datada.

Não usar:
- resultado de eleição como prova de exercício;
- biografia antiga como prova de cargo atual;
- ausência em diretório como prova de que não ocupa cargo.

Registrar separadamente:
- confirmado;
- não confirmado;
- fonte inacessível;
- divergência de fontes.

### F. Oito votações ainda não reconciliadas

Tratar individualmente os oito registros listados em `data/rs/rs-fed-03-targets.json`.

Usar dados oficiais do TSE e identidade composta por, quando disponível:
- ID histórico;
- nome civil;
- cargo;
- localidade eleitoral;
- turno;
- ano.

Não converter ausência em zero. Não atribuir votação da chapa a vice ou suplente.

Se um registro continuar irresolvido, documentar a causa específica.

### G. Links e canais

Ao encontrar canal individual útil durante a pesquisa:
- confirmar identidade antes de publicar;
- manter fonte de proveniência;
- não adivinhar URL;
- não substituir endereço inválido sem confirmação independente;
- não considerar bloqueio HTTP como prova de inexistência.

### H. Integração de dados

Atualizar somente os arquivos pertinentes ao RS, preferencialmente:
- `data/rs/editorial.json`;
- `data/rs/offices-verified.json`;
- históricos/votos quando houver resolução comprovada;
- logs e matrizes do round;
- arquivos gerados em `rs/deputados-federais/`.

Preservar o build determinístico e a separação entre coleta e renderização.

### I. Revisão editorial

Depois da pesquisa, fazer uma passada global nas 107 fichas para verificar:
- atribuição temporal;
- fonte correspondente;
- linguagem neutra;
- ausência de julgamento eleitoral;
- ausência de propaganda;
- consistência entre fichas;
- diferenciação entre proposta, atuação, trajetória e execução.

Não produzir ranking, recomendação ou conclusão sobre em quem votar.

### J. QA

Executar os testes existentes e ampliar quando necessário.

Gates mínimos:
- todos os testes unitários passam;
- 171 verificações Chromium ou cobertura equivalente passam nas larguras já homologadas;
- nenhum overflow horizontal;
- busca, menu, âncoras, fotos, históricos e links permanecem funcionais;
- build repetido gera os mesmos arquivos;
- arquivos de outras frentes permanecem sem regressão.

### K. Integração e publicação

1. Gerar relatório antes/depois.
2. Abrir PR com números de cobertura reais.
3. Não declarar 63/63 resolvidas se houver lacunas.
4. Conferir o `main` imediatamente antes do merge.
5. Integrar apenas após os gates passarem.
6. Confirmar GitHub Pages.
7. Executar verificação pública por hash dos arquivos servidos.
8. Atualizar a issue #1.

## Critério de conclusão do round

O round está executado quando todas as **63 fichas** tiverem sido individualmente pesquisadas nesta rodada e classificadas com um resultado auditável.

Resultados possíveis por ficha:
- síntese de pautas/atuação documentada;
- somente trajetória documentada;
- informação documental insuficiente após pesquisa;
- fonte relevante inacessível;
- conflito de fontes pendente.

O round **não exige inventar conteúdo para chegar a 100% de sínteses**.

A issue #1 só deve ser fechada se, ao final:
- a cobertura editorial for considerada suficiente segundo os critérios documentais;
- as pendências restantes não comprometerem o objetivo originalmente assumido;
- todas as limitações estiverem explicitadas.

Caso contrário, manter a issue aberta com a lista nominal e quantitativa das pendências.

## Entregáveis do RS-FED-03

- base editorial revisada;
- manifesto final dos 63 alvos;
- log individual de pesquisa;
- matriz final antes/depois;
- relatório das oito votações;
- relatório de cargos atuais;
- relatório de fontes rejeitadas/inacessíveis;
- testes;
- QA de navegador;
- PR;
- commit de integração;
- deploy verificado;
- atualização da issue #1;
- pacote reproduzível da frente RS.

## Regra central

**Pesquisar até onde as fontes permitem; nunca transformar ausência de evidência em evidência de ausência.**

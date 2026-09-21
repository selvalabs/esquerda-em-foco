# Protocolo de revisão das pautas — SC federais

Revisão de 21/09/2026. Frente: as 48 fichas de deputados federais por SC já presentes no baseline `810a7896b3355254d50852761a41bae31ce3f567`. Issue #6. Este trabalho não é um novo censo de candidaturas nem uma revalidação da situação de registro eleitoral.

## Objetivo e fronteiras

Aprofundar as sínteses de pautas, registrar evidência por afirmação e preparar uma taxonomia documental preliminar. Não implementar filtros. Preservar nomes de urna, números eleitorais, partidos, histórico, mandatos, imagens, redes, rotação diária, navegação, SEO e contador. Não modificar as frentes estaduais ou de outros estados.

O baseline conserva a descrição anterior de cada pessoa. Nenhuma lista anterior é considerada comprovada apenas porque já estava no site. Quando a nova pesquisa não sustenta um trecho, ele permanece na auditoria, mas não é reapresentado como posição confirmada.

## Pesquisa individual

A primeira passagem usa nome de urna, número, estado e canais previamente cadastrados. A segunda amplia a busca para nome civil, perfis, entrevista e documentos específicos, sobretudo quando a primeira não produz material suficiente. Os percursos efetivamente empregados são registrados em cada ficha; não se apresenta esse registro como log automático exaustivo de todas as consultas do buscador.

Priorizar páginas de campanha, manifestações da própria pessoa, materiais eleitorais, documentos institucionais e entrevistas com declarações identificadas. Uma página partidária só serve quando contém apresentação ou declaração individual daquela candidatura. Programa geral da sigla não preenche lacunas individuais.

Nos casos em que a página depende de JavaScript, a leitura pública em navegador pode complementar a extração simples. Não há login, contato com candidaturas ou tentativa de contornar restrições. Respostas 403/429, exigência de login, conteúdo removido e extração insuficiente são limitações de acesso, não evidência de ausência de posições.

## Identidade, autoria e sentido

Confirmar a correspondência por nome, número, estado, trajetória e canais vinculados. Nome parecido não basta. Exemplos de riscos encontrados: homônimo de outra candidatura, magistrado com nome similar, publicação de prefeitura de outro estado e vídeos sugeridos de outro perfil.

A legenda principal de uma publicação não se confunde com comentários ou vídeos relacionados. Um resultado de busca pode reunir esses textos; só a autoria e o contexto conferidos podem sustentar uma atribuição. Links redirecionados devem registrar o endereço final consultado.

Apoio a um tema amplo não permite deduzir apoio a todas as medidas nele contidas. A oposição a uma medida deve permanecer descrita como oposição, sem ser convertida em apoio genérico ao assunto. Profissão, nome de urna, identidade pessoal, filiação e cargos em entidades não substituem uma declaração de posição.

## Temporalidade

Preferir material de 2026, mas separar o que é apresentação eleitoral de uma manifestação pública fora de campanha. Para fontes antigas, indicar o ano na própria síntese. Não presumir continuidade até 2026. Material conjunto publicado por outra pessoa deve manter essa atribuição e não virar fala individual transcrita.

Quando não há data original, registrar `published_at: null`. Ano de rodapé, data de rastreamento e data da consulta não são data de publicação. Uma indicação relativa, como há dois dias, não foi convertida em uma data exata sem confirmação.

A revisão de pauta não atesta que uma proposta virou lei, que uma realização ocorreu ou que determinada política produzirá o resultado prometido. Essas verificações exigiriam outro escopo e fontes adequadas. Afirmações de eficácia, valores de emendas e estatísticas não necessárias à descrição da posição não foram incorporadas.

## Modelo de evidências

Os arquivos manuais em `data/sc-federais-pautas/inputs/` contêm 48 registros. O compilador adiciona os nomes e dados identificadores do baseline, sem reescrevê-los, e produz `review.json`.

Cada registro conserva: ID da ficha; verificação de identidade; tipo de cobertura documental; percursos de pesquisa; resumo anterior; afirmações revisadas; fontes de cada afirmação; URL, origem, tipo, período, data quando disponível, localizador e data de consulta; limitações; endereços conferidos e atribuições descartadas quando relevantes.

As sínteses são paráfrases curtas. Não armazenar no repositório cópias integrais de sites, entrevistas ou redes sociais. Os registros temporários de leitura em Actions documentam a inspeção técnica; a base editorial durável é formada por paráfrases e referências.

## Cobertura não é avaliação política

Os estados descrevem o tipo de material consultado: campanha, prioridades em ficha, manifestação pública, histórico, apresentação sem data original, material conjunto ou documentação insuficiente. Eles não formam uma escala de mérito e não devem ser ordenados como classificação de candidaturas.

A mensagem de lacuna deve dizer que a documentação acessível foi insuficiente para uma síntese, nunca que a candidatura não tem pautas. Todas as fichas continuam disponíveis na busca e na rotação, inclusive as que permanecem com lacunas.

## Taxonomia preliminar e próxima etapa

As famílias temáticas surgem das afirmações revisadas e estão em `taxonomy-proposal.json`, com contagens documentais separadas entre 2026, histórico, data desconhecida e atribuição conjunta pendente. Não são tags ativas nem autorização para filtrar automaticamente.

Antes dos filtros, revisar fronteiras e equivalências tema a tema, o sentido de apoio/oposição e a temporalidade. Não classificar por expressão regular. Casos como deficiência/ciência, educação para jovens trabalhadores/trabalho em geral e saúde/SUS mostram por que a classificação deve ser explícita e vinculada à evidência.

Para replicação, reutilizar o protocolo e o esquema de dados, não as associações de pessoas ou partidos. Cada nova frente exige seu próprio inventário, pesquisa, verificação de identidade e cobertura.

## Reprodução técnica e revisão

Na raiz do repositório, com Python e BeautifulSoup instalados:

```sh
python tools/sc_federal_pautas/snapshot.py
python tools/sc_federal_pautas/build_review.py
python tools/sc_federal_pautas/qa.py
python tools/sc_federal_pautas/check_links.py
```

O QA de interface também exige Playwright e Chromium. A compilação deve ser idempotente e sua diferença deve se limitar aos blocos autorizados. O relatório técnico registra testes executados e limitações; não se deve inferir teste em navegador ou aparelho não executado.

Publicar apenas depois da revisão do diff e dos testes. Alterações concorrentes no `main` devem ser preservadas por integração da branch, nunca por substituição integral da versão em produção por um snapshot antigo.

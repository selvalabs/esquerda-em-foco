"""Textos editoriais para o modelo dos cards v2, sem publicar a interface.
As referências e vínculos por frase são resolvidos nas decisões, não por palavras-chave.
Cada bloco só existe quando há conteúdo; os 19 casos sem afirmações recebem nota documental.
"""
COPY = {
'240002533824': {
'pautas':'Defende o SUS, os direitos da enfermagem e a valorização permanente do salário mínimo. Também apresenta a proteção às mulheres e o enfrentamento ao casamento infantil entre suas frentes de defesa.',
'historico':'O site relata autoria de projeto sobre climatério no SUS e voto pelo fim da escala 6×1, além de mencionar atuação em justiça climática e prevenção de desastres. São registros apresentados pelo próprio mandato; esta auditoria não confirma votação nominal, aprovação de leis ou resultados de execução.'},
'240002533828': {
'pautas':'Defende o SUS, a valorização dos profissionais da saúde e a proteção jurídica das pessoas transplantadas. Sua apresentação também prioriza educação, serviços públicos, direitos das mulheres, trabalhadores, população LGBTQIA+ e pessoas idosas, além da proteção animal.'},
'240002533825': {
'pautas':'Defende tarifa zero, fim da escala 6×1 e implantação da Casa da Mulher Brasileira em Florianópolis. Também apresenta cultura, direitos LGBTQIA+, democracia e reforma política entre suas prioridades.',
'posicoes':'Declara oposição às bets, à redução da maioridade penal, à ampliação do armamento civil, às escolas cívico-militares e ao ensino domiciliar.'},
'240002533832': {
'pautas':'Defende o fortalecimento dos serviços públicos, com investimento e contratação por concurso na saúde, valorização e formação docente e maior acesso às creches. Propõe ampliar o efetivo e a formação na segurança, prevenir o feminicídio e melhorar o atendimento às vítimas. Na tributação, defende impostos proporcionais à renda e ao patrimônio, além de maior fiscalização das emendas parlamentares.'},
'240002533826': {
'pautas':'Defende o SUS e os serviços públicos, a valorização dos profissionais da saúde e a proteção dos direitos das mulheres e dos trabalhadores.',
'posicoes':'Apresenta a pré-candidatura como uma construção coletiva, com participação de apoiadores. Esse modelo de campanha não é apresentado aqui como uma proposta de participação na gestão pública.'},
'240002533830': {
'pautas':'Defende demarcação e proteção de territórios, apoio à agroecologia e à pesca artesanal, recuperação de rios e florestas e prevenção de desastres. Propõe infraestrutura comunitária de cuidado, água e saneamento, saúde e educação interculturais. Também defende igualdade salarial e enfrentamento à violência contra mulheres, com atenção às responsáveis por famílias nas políticas de prevenção.',
'posicoes':'Declara oposição ao Marco Temporal.'},
'240002533827': {
'pautas':'Na ficha de prioridades de 2026, apresenta cidadania LGBTQIA+, direitos das mulheres, cultura e educação. Também indica infância, juventude e cidadania no envelhecimento. A página enumera essas prioridades, sem detalhar medidas legislativas para cada uma.'},
'240002533823': {
'historico':'Em pronunciamento de outubro de 2023 registrado pela Alesc, defendeu educação, juventude, proteção às mulheres e maior participação de mulheres negras na vida pública. O discurso não é apresentado como programa federal de 2026.'},
'240002533833': {
'posicoes':'Em manifestação de julho de 2026, defendeu intervenção contra as bets, incluindo sua proibição.',
'historico':'Em 2026, apresentou um requerimento de seminário sobre o PNE e publicou convocação de assembleia de orçamento participativo. Esses documentos comprovam iniciativas, não a aprovação do plano nem a realização do encontro. No histórico anterior, há defesa de fomento a sistemas agroflorestais em 2023 e registro autoral de apoio ao piso da enfermagem em 2022.'},
'240002533831': {
'pautas':'Defende o SUS, o fim da escala 6×1 e o enfrentamento à LGBTfobia e à violência contra mulheres. Em entrevista individual de 2026, também defende acesso dos jovens à educação e ao trabalho digno e a aplicação de políticas de proteção às mulheres.'},
'240002537831': {
'pautas':'Defende preservar e reutilizar a Antiga Rodoviária de Florianópolis como patrimônio de uso público e manter espaços e funções públicas no centro. Também valoriza a participação social por associações de bairro e organização comunitária.',
'historico':'Na entrevista de fevereiro de 2026, relata ter produzido um vídeo sobre extravasamento de esgoto na Lagoa da Conceição e cobrado estrutura, servidores e investimento para a política ambiental em audiência na Alesc. O relato não informa a data exata de cada ação.'},
'240002537839': {
'pautas':'Defende o fim da escala de trabalho 6×1. A manifestação localizada trata dessa pauta específica.'},
'240002537832': {
'pautas':'Apresenta educação pública, cultura, direitos humanos, democracia, direitos LGBTQIA+, juventude, meio ambiente e saúde pública/SUS entre suas prioridades. Também defende participação popular nas decisões políticas.',
'historico':'Sua apresentação relata mobilizações estudantis contra cortes na educação em 2018–2019. Esse percurso é separado das prioridades atuais.'},
'240002537838': {
'pautas':'Defende os direitos das mulheres e da população LGBTQIA+, democracia e liberdade de expressão. Também apresenta cultura popular, comunicação livre, trabalho digno, justiça climática, agroecologia e saúde pública entre suas bandeiras.'},
'240002537830': {
'historico':'Em manifestação registrada em 2023, defendeu acesso e permanência de pessoas trans e travestis na universidade e o enfrentamento à transfobia. Trata-se de atuação histórica, não de confirmação automática de um programa de campanha atual.'},
'240002537841': {
'pautas':'Defende um Museu dos Povos Originários em SC, reconhecimento e proteção de territórios indígenas e quilombolas e fortalecimento da Funai e da Sesai. Na produção rural, propõe apoio à agricultura familiar, à reforma agrária e à agroecologia. Suas bandeiras incluem moradia popular, acessibilidade para pessoas com deficiência e idosas, cannabis medicinal, atendimento às mulheres, enfrentamento ao feminicídio e justiça climática.'},
'240002537836': {
'pautas':'Defende planejamento urbano comprometido com o direito à cidade, a inclusão social e a dimensão metropolitana, ampliando o diálogo com moradores, movimentos sociais, universidades e técnicos públicos.',
'posicoes':'Na carta de abril de 2026, critica a concentração territorial de investimentos e alerta para o risco de expulsão de moradores. O diagnóstico não é apresentado como uma proposta orçamentária específica para as periferias.'},
'240002533820': {
'historico':'A revisão anterior registrou pedidos municipais de pavimentação e de alteração de tampas de drenagem apresentados em 2023. A fonte não pôde ser reconferida nesta auditoria; o registro permanece com essa ressalva e não alimenta filtros atuais.'},
'240002543042': {
'pautas':'Defende identificar precocemente a violência psicológica e patrimonial, integrar a rede de proteção e ampliar recursos para atendimento e medidas protetivas. Propõe qualificação profissional, autonomia econômica, assistência jurídica e acolhimento às vítimas, além de dados sobre violência e ações contra a reincidência dos agressores.'},
'240002541412': {
'contexto':'A apresentação individual relata atuação por investimento na educação pública e condições de acesso e permanência de jovens trabalhadores. O período original do material não foi confirmado; ele não é classificado automaticamente como programa de 2026 nem como documento de um ano histórico determinado.'},
'240002539586': {
'contexto':'A apresentação individual defende direitos dos trabalhadores, enfrentamento aos baixos salários e ao custo de vida e reforma urbana para ampliar o acesso à cidade. O material não tem período original confirmado.'},
'240002553721': {
'contexto':'A apresentação individual defende reverter privatizações e reestatizar empresas e declara uma orientação anti-imperialista. Seu período original não foi confirmado; não se presume apoio a governos ou medidas internacionais não identificadas.'},
'240002553720': {
'contexto':'A apresentação individual defende ingresso universitário sem vestibular, jornada de 35 horas e transporte gratuito para desempregados e trabalhadores informais. Também trata de liberdade de expressão, oposição à censura e apoio a povos que identifica como resistentes ao imperialismo. O período do material permanece indeterminado.'},
'240002533829': {
'posicoes':'Apresenta a intenção de levar sua experiência de atuação municipal para Brasília.',
'historico':'Em uma publicação de apresentação, relata reunião na qual discutiu investimentos em saúde, educação e infraestrutura para Balneário Camboriú e região. Os assuntos do encontro não são convertidos, por si só, em novos compromissos setoriais de campanha.'},
'240002533838': {
'pautas':'Declara compromisso com a educação pública e com a participação da população nas decisões políticas. O material consultado não detalha instrumentos legislativos para essas prioridades.'},
'240002537826': {
'pautas':'A Coletiva SC Plural apresenta o cuidado como prioridade política e defende maior participação de mulheres e mães nos espaços de decisão. Essa declaração não é ampliada para propostas de creches ou licenças não mencionadas.'},
'240002537827': {
'pautas':'Defende o fim da escala 6×1, com 40 horas semanais, dois dias de descanso e manutenção salarial. Também defende a permanência das cotas raciais nas universidades de Santa Catarina.'},
'240002537840': {
'contexto':'Uma publicação conjunta de campanha atribui a Thiago Moreti defesa de educação plural, valorização docente e liberdade pedagógica. O material foi publicado por outro participante; não foi tratado como uma declaração individual transcrita da candidatura.'},
'240002537833': {
'pautas':'Defende o fim da escala 6×1, direitos dos trabalhadores por aplicativo, tarifa zero e ampliação de investimentos em saúde e educação.',
'posicoes':'Defende combater as bets e os jogos de azar.'}
}

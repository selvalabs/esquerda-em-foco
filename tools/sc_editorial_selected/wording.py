"""Camada de leitura da #36. Cada parágrafo referencia itens aprovados, não palavras.
Não altera a auditoria, fontes, famílias, elegibilidade ou os registros eleitorais.
Avisos indispensáveis permanecem junto do texto; detalhes vão para Fontes e contexto.
"""
BASE = 'd8bf0ae43a24f0f8f297316bb366e497dc3dfc8c'
LABELS = {'pautas':'Pautas atuais','posicoes':'Outras posições','historico':'Atuação registrada','contexto':'Sobre este material'}
GAP = 'Neste levantamento, não encontramos material individual suficiente para resumir as pautas. Isso não significa que a candidatura não tenha propostas.'
CONTEXT_INTRO = 'Encontramos material com data ou autoria ainda não confirmadas. Ele pode ser consultado em Fontes e contexto, mas não entra nos filtros de pautas atuais.'
# (itens, texto). Itens suplementares continuam sem associação temática.
COPY = {
'240002541412': {'contexto': {
'p': [('item1','A apresentação de Amanda relata mobilização por mais investimento na educação pública e por condições de acesso e permanência de jovens trabalhadores.')],
'notice':'Não foi possível confirmar o período desse material. Ele não é apresentado como programa de 2026.',
'note':'A falta de data também não permite atribuir a apresentação a uma eleição anterior.'}},
'240002553721': {'contexto': {
'p': [('item1','Na apresentação consultada, Ana Paula Adão defende reverter privatizações e reestatizar empresas.'),('item2','Em política internacional, declara uma orientação anti-imperialista.')],
'notice':'O período original da apresentação não foi confirmado.',
'note':'Essa autodefinição não permite atribuir apoio a governos ou medidas internacionais que o material não identifica.'}},
'240002533824': {
'pautas': {'p': [('item1 item2 item6','Na saúde e no trabalho, defende o SUS, os direitos da enfermagem e a valorização permanente do salário mínimo.'),('item3 item4','A proteção às mulheres, o enfrentamento à violência e a proteção de meninas e adolescentes contra o casamento infantil também aparecem entre suas pautas.')]},
'historico': {'p': [('item5 extra1','O site do mandato relata a autoria de um projeto sobre atendimento do climatério pelo SUS e um voto pelo fim da escala 6×1.'),('item7','A página também menciona atuação em justiça climática e prevenção de desastres.')],
'notice':'Esses registros são do próprio mandato. A votação nominal, a aprovação de leis e os resultados de execução não foram conferidos nesta revisão.',
'note':'A atribuição ao site é parte da informação e não deve ser retirada ao resumir ou compartilhar a ficha.'}},
'240002543042': {'pautas': {
'p': [('item1 item2','Para enfrentar a violência contra mulheres, propõe identificar mais cedo a violência psicológica e patrimonial, integrar a rede de proteção e ampliar recursos para atendimento e medidas protetivas.'),('item3 item4','Também defende assistência jurídica, acolhimento, qualificação profissional e autonomia econômica para as vítimas.'),('item5','Entre as propostas estão ainda dados sobre violência e ações para reduzir a reincidência dos agressores.')] }},
'240002539586': {'contexto': {
'p': [('item1','Na apresentação individual, Andre defende os direitos dos trabalhadores e o enfrentamento aos baixos salários e ao custo de vida.'),('item2','Na área urbana, propõe reforma urbana e maior acesso à cidade.')],
'notice':'Não foi possível confirmar o período original dessa apresentação.'}},
'240002553720': {'contexto': {
'p': [('item1 item2 item3','Na apresentação consultada, Arthur defende jornada de 35 horas semanais, ingresso universitário sem vestibular e transporte gratuito para desempregados e trabalhadores informais.'),('item4 item5','Também se posiciona pela liberdade de expressão e contra a censura. Em política internacional, declara apoio a povos que identifica como resistentes ao imperialismo.')],
'notice':'O período original do material não foi confirmado.',
'note':'A gratuidade mencionada tem públicos específicos. O posicionamento internacional mantém a atribuição e os limites da apresentação.'}},
'240002533828': {'pautas': {
'p': [('item1 item2','Na saúde, defende o SUS, a valorização dos profissionais e um estatuto específico de proteção jurídica às pessoas transplantadas.'),('item3 item4 item5 item7','Sua apresentação também inclui a defesa de mulheres, trabalhadores, servidores públicos, população LGBTQIA+ e pessoas idosas.'),('item6 item8 item9','Educação, serviços públicos e proteção animal completam as prioridades registradas neste levantamento.')],
'note':'A proposta de estatuto não é apresentada como lei em vigor. A lista resume o material consultado, não pretende esgotar as pautas da candidatura.'}},
'240002533825': {
'pautas': {'p': [('item1 item2 item3','Entre as propostas estão tarifa zero no transporte público, fim da escala 6×1 e implantação da Casa da Mulher Brasileira em Florianópolis.'),('item4 item5 item6','Cultura, direitos LGBTQIA+, democracia e reforma política também aparecem como prioridades.')]},
'posicoes': {'p': [('item7 item9 item10','Declara oposição às bets, à redução da maioridade penal e à ampliação do armamento civil.'),('item8','Na educação, se posiciona contra escolas cívico-militares e ensino domiciliar.')] }},
'240002537831': {
'pautas': {'p': [('item1 item2','No centro de Florianópolis, defende preservar e reutilizar a Antiga Rodoviária como patrimônio de uso público e manter espaços e funções públicas na região.'),('item4','Também defende a participação social por associações de bairro e organização comunitária.')]},
'historico': {'p': [('item3 item5','Em entrevista de fevereiro de 2026, relata ter produzido um vídeo sobre extravasamento de esgoto na Lagoa da Conceição e cobrado estrutura, servidores e investimento para a política ambiental em audiência na Alesc.')],
'notice':'A entrevista não informa a data exata de cada ação.',
'note':'São relatos de atuação. A data da entrevista não é usada como data dos acontecimentos.'}},
'240002533829': {
'posicoes': {'p': [('extra1','Diz que pretende levar sua experiência de atuação municipal para Brasília.')]},
'historico': {'p': [('item1','Em uma publicação de apresentação, relata uma reunião sobre investimentos em saúde, educação e infraestrutura para Balneário Camboriú e região.')],
'notice':'O registro descreve o encontro; não detalha novos compromissos para cada área.',
'note':'O assunto de uma reunião não é usado, por si só, como pauta atual para os filtros.'}},
'240002537839': {'pautas': {'p': [('item1','Na manifestação consultada, defende o fim da escala de trabalho 6×1.')],
'note':'A síntese se limita à manifestação localizada; não é uma lista completa de propostas.'}},
'240002533831': {'pautas': {
'p': [('item1 item2 item3 item4','O site apresenta a defesa do SUS, o fim da escala 6×1 e o enfrentamento à LGBTfobia e à violência contra mulheres.'),('item5 item6 item7 item8','Em entrevista de 2026, também defende ampliar o acesso dos jovens à educação e ao trabalho digno e aplicar políticas de proteção às mulheres.')] }},
'240002537832': {
'pautas': {'p': [('item2 item3 item7 item8 item9','Educação pública, cultura, juventude, meio ambiente e saúde pública, com defesa do SUS, estão entre as prioridades de sua apresentação.'),('item1 item4 item5 item6','Na área de direitos, inclui direitos humanos e LGBTQIA+, defesa da democracia e participação popular nas decisões políticas.')]},
'historico': {'p': [('extra1','A apresentação relata mobilizações estudantis contra cortes na educação em 2018–2019.')],
'note':'O período histórico está expresso e não substitui as prioridades atuais.'}},
'240002533820': {'historico': {
'p': [('item1','O levantamento anterior registrou pedidos municipais de pavimentação e de alteração de tampas de drenagem apresentados em 2023.')],
'notice':'A fonte não pôde ser reconferida na última revisão. O registro permanece com essa ressalva e não entra nos filtros atuais.'}},
'240002537838': {'pautas': {
'p': [('item1 item2 item3 item4 item8','Sua apresentação reúne a defesa dos direitos das mulheres e da população LGBTQIA+, da democracia, da liberdade de expressão e de uma comunicação livre.'),('item5 item6 item7 item9 item10','Também traz cultura popular, trabalho digno, justiça climática, incentivo à agroecologia e fortalecimento da saúde pública entre suas bandeiras.')] }},
'240002533832': {'pautas': {
'p': [('item2 item4','Na saúde, defende mais investimento, estrutura pública e contratação por concurso, como parte de sua defesa dos serviços públicos.'),('item1 item6 item7','Na educação, propõe investimento, valorização e formação docente e ampliação do acesso às creches.'),('item3 item5','Para a segurança, propõe ampliar o efetivo e a formação continuada dos profissionais. Também defende prevenção ao feminicídio e maior atendimento às vítimas de violência.'),('item8 item9','Na área econômica, defende impostos proporcionais à renda e ao patrimônio. Também propõe maior fiscalização das emendas parlamentares.')] }},
'240002533826': {
'pautas': {'p': [('item1 item2 item3','SUS, serviços públicos e valorização dos profissionais da saúde estão entre as pautas de sua apresentação.'),('item5 item6','Também defende ampliar os direitos das mulheres e proteger os direitos dos trabalhadores.')]},
'posicoes': {'p': [('item4','Apresenta sua pré-candidatura como uma construção coletiva, com participação de apoiadores.')],
'note':'A frase descreve a construção da campanha, não uma proposta de participação na gestão pública.'}},
'240002533830': {
'pautas': {'p': [('item1 item2 item4','Na área de territórios e produção, defende demarcação e proteção de terras indígenas, quilombolas e de comunidades tradicionais, apoio à agroecologia e à pesca artesanal e recuperação de rios e florestas.'),('item3 item5 item6 item7','Propõe prevenção de desastres com atenção às mulheres responsáveis por famílias. Também defende acesso à água e ao saneamento e infraestrutura comunitária de cuidado.'),('item8 item9 item10 item11','Em saúde e educação, defende políticas interculturais, que respeitem as culturas e os modos de vida dos povos. Igualdade salarial entre mulheres e homens e enfrentamento à violência contra mulheres também estão entre suas pautas.')]},
'posicoes': {'p': [('extra1','Se posiciona contra o Marco Temporal.')] }},
'240002533827': {'pautas': {
'p': [('item1 item2 item3 item4','Na ficha de prioridades de 2026, indica cultura, educação, direitos das mulheres e cidadania LGBTQIA+.'),('item5 item6','Infância, juventude e cidadania no envelhecimento também aparecem na ficha.')],
'note':'A página enumera prioridades, sem detalhar medidas legislativas para cada uma. O texto preserva esse grau de generalidade.'}},
'240002537826': {'pautas': {
'p': [('item1 item2','Para a Coletiva SC Plural, o cuidado é uma prioridade política. A apresentação também defende maior participação de mulheres e mães nos espaços de decisão.')],
'note':'A declaração não menciona medidas específicas de creches ou licenças; elas não foram acrescentadas à síntese.'}},
'240002537827': {'pautas': {
'p': [('item1','No trabalho, defende o fim da escala 6×1, com 40 horas semanais, dois dias de descanso e manutenção salarial.'),('item2','Na educação, defende manter as cotas raciais nas universidades de Santa Catarina.')] }},
'240002537830': {'historico': {
'p': [('item1','Em manifestação registrada em 2023, defendeu acesso e permanência de pessoas trans e travestis na universidade e o enfrentamento à transfobia.')],
'note':'O registro é histórico e não é apresentado como confirmação de um programa de campanha atual.'}},
'240002537841': {'pautas': {
'p': [('item1 item2','Defende a criação de um Museu dos Povos Originários em Santa Catarina e o reconhecimento e a proteção de territórios indígenas e quilombolas.'),('item3 item4','Para Funai e Sesai, propõe mais orçamento, equipes e valorização dos servidores, incluindo o reforço da saúde indígena.'),('item5','Na produção rural, defende agricultura familiar, reforma agrária e agroecologia, com assistência técnica, crédito e apoio à comercialização.'),('item6 item7 item8 item9 item10 item11','Também apresenta moradia popular, acessibilidade para pessoas com deficiência e idosas, cannabis medicinal, atendimento às mulheres, enfrentamento ao feminicídio e justiça climática entre suas bandeiras.')] }},
'240002533838': {'pautas': {
'p': [('item1 item2','Educação pública e participação da população nas decisões políticas são os compromissos expressos no material consultado.')],
'note':'O material não detalha instrumentos legislativos para essas prioridades.'}},
'240002533823': {'historico': {
'p': [('item1','Em pronunciamento de outubro de 2023 registrado pela Alesc, defendeu educação, juventude, proteção às mulheres e maior participação de mulheres negras na vida pública.')],
'note':'O discurso de 2023 não é apresentado como programa federal de 2026.'}},
'240002537836': {
'pautas': {'p': [('item1 item2','Para o planejamento urbano, defende direito à cidade, inclusão social e atenção à dimensão metropolitana, com mais diálogo entre moradores, movimentos sociais, universidades e técnicos públicos.')]},
'posicoes': {'p': [('item3','Na carta de abril de 2026, critica a concentração territorial dos investimentos e alerta para o risco de expulsão de moradores.')],
'note':'A crítica não foi transformada em uma proposta orçamentária específica para as periferias.'}},
'240002533833': {
'posicoes': {'p': [('item3','Em julho de 2026, defendeu intervenção contra as bets, incluindo sua proibição.')]},
'historico': {'p': [('item1 item2','Em 2026, apresentou um requerimento de seminário sobre o Plano Nacional de Educação e os planos estadual e municipal. Seu mandato também publicou uma convocação de assembleia de orçamento participativo em junho daquele ano.'),('item4 item5','Em registros anteriores, há defesa de fomento a sistemas agroflorestais, em 2023, e relato do próprio mandato de apoio ao piso da enfermagem, em 2022.')],
'notice':'O requerimento não comprova a aprovação do plano, e a convocação não comprova que a assembleia ocorreu.',
'note':'O registro sobre a enfermagem é atribuído ao mandato, não apresentado como nova conferência independente de votação nominal.'}},
'240002537840': {'contexto': {
'p': [('item1','Uma publicação conjunta de campanha apresenta Thiago Moreti como defensor de educação plural, valorização docente e liberdade pedagógica.')],
'notice':'O material foi publicado por outro participante da campanha. Não foi confirmado como declaração individual transcrita de Thiago.'}},
'240002537833': {
'pautas': {'p': [('item1 item2','No trabalho e no transporte, defende o fim da escala 6×1, os direitos dos trabalhadores por aplicativo e tarifa zero no transporte público.'),('item3 item4','Também propõe ampliar os investimentos em saúde e educação.')]},
'posicoes': {'p': [('item5','Se posiciona pelo combate às bets e aos jogos de azar.')] }}
}

UI_COPY = {
'preview_label':'Prévia de trabalho · não publicada',
'intro_title':'Fichas para consultar com calma',
'intro_text':'Abra uma candidatura para ler suas pautas, sua atuação e as fontes. Você pode reunir fichas em Selecionados para voltar a elas durante esta visita.',
'search_label':'Buscar pelo nome',
'selection_title':'Selecionados',
'selection_intro':'Aqui estão as fichas que você reuniu. Abra uma de cada vez; a ordem segue a sua seleção.',
'empty_title':'Você ainda não selecionou nenhuma ficha',
'empty_text':'Volte à lista e use Selecionar nas fichas que deseja consultar.',
'privacy_notice':'A coleção fica apenas nesta página e se perde ao recarregar. Um link compartilhado permite abri-la novamente. Quem receber o link poderá ver os itens incluídos.',
'source_details':'Fontes e contexto',
'context_details':'O que foi possível confirmar',
'filter_context':'Trecho relacionado à área escolhida',
'filter_disclaimer':'O destaque indica o trecho, não apoio a todos os assuntos do grupo.',
'no_section':'Não encontramos registro suficiente desta seção no levantamento consultado.',
'model_notice':'Conteúdo do levantamento revisado em 21/09/2026. A revisão de linguagem não atualiza as posições políticas.',
'prototype_share':'Links de coleção desta prévia são apenas para teste. O compartilhamento público de Selecionados será habilitado na integração ao site.'
}

EDITORIAL_DECISIONS = [
{'id':'title-history','decision':'Usar Atuação registrada, não Atuação anterior.','reason':'O bloco inclui iniciativas de 2026 e relatos sem data exata; anterior pode sugerir outro mandato ou posição abandonada.'},
{'id':'current-window','decision':'Manter Pautas atuais com a data do levantamento visível.','reason':'Atual refere-se ao recorte documentado, não a monitoramento contínuo.'},
{'id':'meaningful-warnings','decision':'Manter ressalvas determinantes junto do texto.','reason':'Autoria atribuída, data desconhecida e falta de reconferência não podem ficar escondidas para melhorar a fluidez.'},
{'id':'sources','decision':'Uma referência legível por fonte pertinente ao parágrafo.','reason':'O rótulo usa tipo e data original quando confirmada; nunca a data de consulta como data da publicação.'},
{'id':'highlight','decision':'Mapear cada parágrafo aos itens/associações para reduzir repetição no motivo do filtro.','reason':'No Round 2, marcar somente parágrafos sustentados pelos IDs. Nenhuma correspondência por palavra, fonte inteira ou simples vizinhança.'},
{'id':'gap-copy','decision':'Usar o mesmo aviso curto nas 19 lacunas.','reason':'Variação cosmética criaria diferenças aparentes onde o resultado documental é o mesmo.'},
{'id':'selection-reader','decision':'Coleção com leitura individual e compartilhamento, sem comparação entre candidaturas.','reason':'Uma ficha visível por vez; não sincronizar seções entre pessoas nem produzir diferenças, notas ou recomendações.'}
]

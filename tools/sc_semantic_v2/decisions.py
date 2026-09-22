"""Decisões editoriais explícitas da #32, Round 1; não é um classificador.
Cada linha identifica claim, famílias, natureza, frase final e justificativa/localizador.
A/P = apoio/prioridade atual; C/O = posição/oposição; T/H = atuação/histórico;
U/J = período indeterminado/atribuição conjunta, conservados em contexto.
Os IDs e fontes de origem nunca são substituídos por uma busca por palavras.
"""
REVIEW_DATE = '2026-09-21'
BASE = '32175f20f594f48bf101144809fb9d39d71c94a6'
D = {}

def candidate(cid, rows):
    assert cid not in D
    D[cid] = rows

candidate('240002533824', [
('c1','A','direitos-trabalhistas','Defende os direitos dos profissionais da enfermagem.','Propósito / Saúde Pública: defesa expressa, não inferida da profissão.'),
('c1','A','saude','Defende o fortalecimento do SUS.','Propósito / Saúde Pública: separar defesa do SUS dos resultados de emendas para atenção básica.'),
('c2','P','direitos-mulheres','Apresenta os direitos das mulheres e o enfrentamento à violência como frentes de defesa.','Apresentação atual e Propósito / Mulheres; autoria de projetos não é apresentada como realização verificada.'),
('c2','A','infancia-juventude','Defende a proteção de meninas e adolescentes contra o casamento infantil.','Propósito / Mulheres: atuação contra o casamento infantil é explicitamente reiterada como propósito.'),
('c2','T','saude','Seu site relata a autoria de um projeto sobre atendimento do climatério pelo SUS.','Propósito / Mulheres: o texto é de autoria de projeto, não de nova proposta; não confirma aprovação nem execução.'),
('c3','A','direitos-trabalhistas','Defende a valorização permanente do salário mínimo.','Propósito / Justiça Social: manter a defesa explícita; separar a alegação de voto sobre 6×1 do mesmo grupo original.'),
('c3','T','meio-ambiente-clima prevencao-desastres','O site apresenta justiça climática e prevenção de desastres entre as áreas de sua atuação.','Trajetória Política: descrição genérica de atuação, sem objeto programático próprio; não promover a proposta atual.')])

candidate('240002533828', [
('c1','A','direitos-trabalhistas','Defende a valorização dos profissionais da saúde.','Página sobre a pessoa transplantada: defesa expressa; não deduzida de currículo.'),
('c1','A','saude','Defende o SUS e a proteção jurídica das pessoas transplantadas por um estatuto específico.','Pessoa Transplantada e debate de 2026; proposta não é descrita como lei em vigor.'),
('c2','P','direitos-lgbtqia','Inclui a defesa da população LGBTQIA+ entre suas prioridades.','Apresentação / Por que sou candidata: prioridade nominal explícita.'),
('c2','P','direitos-mulheres','Inclui os direitos das mulheres entre suas prioridades.','Apresentação: compromisso declarado; não presume posição sobre medidas não citadas.'),
('c2','P','direitos-trabalhistas','Defende trabalhadores e servidores públicos.','Apresentação: públicos expressamente citados, não inferência pela ocupação.'),
('c2','P','educacao','Apresenta a educação como uma de suas prioridades.','Apresentação: prioridade ampla válida; não exigir mecanismo legislativo para um filtro amplo.'),
('c2','P','pessoas-idosas','Inclui a defesa das pessoas idosas entre suas prioridades.','Apresentação: público nomeado, não deduzido de políticas de cuidado.'),
('c2','P','protecao-animal','Apresenta a proteção animal entre suas prioridades.','Apresentação: bandeira expressa, sem inventar medidas específicas.'),
('c2','P','servicos-publicos','Defende os serviços públicos e seus servidores.','Apresentação: defesa expressa; não se confunde com posição sobre privatização de toda empresa.')])

candidate('240002533825', [
('c1','A','direitos-mulheres','Defende a implantação da Casa da Mulher Brasileira em Florianópolis.','QueroApoiar / Sou a favor e artigo individual de 01/04/2026; fontes convergem para a medida.'),
('c1','A','direitos-trabalhistas','Defende o fim da escala de trabalho 6×1.','QueroApoiar / Sou a favor: posição afirmativa explícita.'),
('c1','A','mobilidade-transporte','Defende tarifa zero no transporte público.','QueroApoiar / Sou a favor: gratuidade explicitada, não apenas menção a transporte.'),
('c2','P','cultura','Inclui a cultura entre suas prioridades.','QueroApoiar / prioridades: categoria declarada pela candidatura.'),
('c2','A','democracia-participacao','Defende a democracia e a reforma política.','QueroApoiar / prioridades e Sou a favor; não resulta da simples participação eleitoral.'),
('c2','P','direitos-lgbtqia','Inclui os direitos LGBTQIA+ entre suas prioridades.','QueroApoiar / prioridades: manifestação, não identidade pessoal.'),
('c3','O','apostas-jogos','Declara oposição às bets.','QueroApoiar / Sou contra: preservar o sentido; não apresentar apoio às apostas.'),
('c3','O','educacao','Declara oposição às escolas cívico-militares e ao ensino domiciliar.','QueroApoiar / Sou contra: não deduzir adesão a todas as políticas educacionais.'),
('c3','O','infancia-juventude','Declara oposição à redução da maioridade penal.','QueroApoiar / Sou contra: conservar objeto penal, não inventar programa geral de juventude.'),
('c3','O','seguranca-politica-penal','Declara oposição à redução da maioridade penal e à ampliação do armamento civil.','QueroApoiar / Sou contra: evidência de oposição, não de apoio às medidas.')])

candidate('240002533832', [
('c1','P','educacao','Apresenta investimentos na educação pública como uma de suas bandeiras.','Entrevista / abertura e Propostas: não generalizar contratação na saúde para equipes de toda a educação.'),
('c1','A','saude','Defende mais investimento em saúde, estrutura pública e contratação de profissionais por concurso.','Entrevista / Propostas, primeiro parágrafo: medidas individualmente atribuídas.'),
('c1','A','seguranca-politica-penal','Propõe ampliar o efetivo e a formação continuada dos profissionais de segurança.','Entrevista / Propostas: efetivo e formação, sem inventar uma orientação penal completa.'),
('c1','P','servicos-publicos','Defende o fortalecimento dos serviços públicos.','Entrevista / fala sobre responsabilidade do Estado e propostas setoriais; compromisso expresso.'),
('c2','A','direitos-mulheres','Defende prevenção ao feminicídio e ampliação do atendimento às vítimas de violência.','Entrevista / último parágrafo de Propostas: prevenção e atendimento, não resultados realizados.'),
('c2','A','educacao','Defende valorização e formação docente e maior acesso às creches.','Entrevista / Propostas: escopo específico da educação.'),
('c2','A','infancia-juventude','Defende ampliar o acesso às creches.','Entrevista / Propostas: infância delimitada pela medida, sem estender a toda política de juventude.'),
('c3','A','democracia-participacao','Defende maior fiscalização das emendas parlamentares.','Entrevista / parágrafo da reforma tributária: fiscalização é distinta da proposta de impostos.'),
('c3','A','tributacao','Defende impostos proporcionais à renda e ao patrimônio.','Entrevista / Propostas, reforma tributária: o tema é política tributária, não declaração patrimonial da candidata.')])

candidate('240002533826', [
('c1','A','direitos-trabalhistas','Defende a valorização dos profissionais da saúde.','QueroApoiar / convite final: posição expressa, não consequência de ser técnica de enfermagem.'),
('c1','A','saude','Defende o fortalecimento do SUS.','QueroApoiar / apresentação individual: defesa expressa.'),
('c1','P','servicos-publicos','Defende os serviços públicos.','QueroApoiar / convite final: defesa explícita.'),
('c2','C','democracia-participacao','Apresenta sua pré-candidatura como uma construção coletiva, baseada na participação de apoiadores.','QueroApoiar / construção da campanha: não é proposta específica de participação na gestão pública.'),
('c2','A','direitos-mulheres','Defende ampliar os direitos das mulheres.','QueroApoiar / convite final: compromisso político expresso.'),
('c2','A','direitos-trabalhistas','Defende a proteção dos direitos dos trabalhadores.','QueroApoiar / apresentação e convite final: não ampliar para uma medida trabalhista não citada.')])

candidate('240002533830', [
('c1','A','povos-indigenas-tradicionais','Defende demarcar e proteger territórios indígenas, quilombolas e de comunidades tradicionais.','Propostas / territórios: separar a medida afirmativa da oposição ao Marco Temporal.'),
('c2','A','agricultura-agroecologia','Defende apoio à agroecologia e à pesca artesanal.','Propostas / produção e territórios: atividades nomeadas expressamente.'),
('c2','A','direitos-mulheres','Propõe atenção às mulheres responsáveis por famílias nas políticas de prevenção de desastres.','Propostas / justiça climática e mulheres: destinatárias expressamente identificadas.'),
('c2','A','meio-ambiente-clima','Defende recuperar rios e florestas.','Propostas / justiça climática: restauração explicitada.'),
('c2','A','prevencao-desastres','Defende políticas de prevenção de desastres.','Propostas / justiça climática: medida expressa, não inferida da defesa ambiental.'),
('c3','A','agua-saneamento','Defende acesso à água e ao saneamento.','Propostas / infraestrutura comunitária: não confundir restauração de rios com abastecimento.'),
('c3','A','cuidado-protecao-social','Propõe infraestrutura comunitária para o cuidado.','Propostas / cuidado: compromisso explícito, não inferido da maternidade.'),
('c3','A','direitos-mulheres','Defende igualdade salarial e enfrentamento à violência contra mulheres.','Propostas / mulheres: duas medidas expressas.'),
('c3','A','direitos-trabalhistas','Defende igualdade salarial entre mulheres e homens.','Propostas / mulheres: conservar o objeto salarial, sem atribuir toda reforma trabalhista.'),
('c3','A','educacao','Defende educação intercultural.','Propostas / cuidado e direitos: respeito aos modos de vida explicitado.'),
('c3','A','saude','Defende atenção à saúde que respeite as culturas e os modos de vida dos povos.','Propostas / saúde intercultural: não ampliar automaticamente para toda política de saúde.')])

candidate('240002533827', [
('c1','P','cultura','Apresenta a cultura como prioridade do mandato.','VoteLGBT / Prioridades do mandato: declaração temática ampla válida.'),
('c1','P','direitos-lgbtqia','Apresenta a cidadania LGBTQIA+ como prioridade do mandato.','VoteLGBT / Prioridades: não utilizar os campos de identidade pessoal como evidência.'),
('c1','P','direitos-mulheres','Apresenta os direitos das mulheres como prioridade.','VoteLGBT / Prioridades: tema nominal, sem instrumentos adicionais inventados.'),
('c1','P','educacao','Apresenta a educação como prioridade do mandato.','VoteLGBT / Prioridades: categoria expressa; generalidade não a torna inválida.'),
('c2','P','infancia-juventude','Apresenta infância e juventude como prioridades.','VoteLGBT / Prioridades: não pressupõe medidas específicas de creches ou emprego.'),
('c2','P','pessoas-idosas','Apresenta a cidadania no envelhecimento como prioridade.','VoteLGBT / Prioridades: público explícito, sem inferência a partir da idade.')])

candidate('240002533823', [
('c1','H','educacao infancia-juventude direitos-mulheres igualdade-racial democracia-participacao','Em discurso de 2023 registrado pela Alesc, defendeu educação, juventude, proteção às mulheres e participação de mulheres negras na vida pública.','Alesc, 19/10/2023 / Causa negra como missão: fala histórica, não confirmação de plataforma de 2026.')])

candidate('240002533833', [
('c1','T','educacao','Apresentou em 2026 um requerimento de seminário sobre o PNE e os planos de educação.','Câmara / REQ 23/2026 CE: requerimento de debate, não aprovação do plano nem promessa de campanha.'),
('c1','T','democracia-participacao','Seu mandato publicou uma convocação de assembleia de orçamento participativo em junho de 2026.','Edital Serramar: prova a convocação, não a realização do encontro nem uma nova proposta eleitoral.'),
('c1','O','apostas-jogos','Em julho de 2026, defendeu intervenção contra as bets, incluindo sua proibição.','Manifestação autoral sobre bets: oposição à atividade, não apoio às apostas; estatísticas não são reproduzidas.'),
('c2','H','agricultura-agroecologia meio-ambiente-clima','Em 2023, defendeu fomento a sistemas agroflorestais.','Artigo de 12/09/2023: manifestação histórica, sem reafirmação atual validada nesta associação.'),
('c2','H','direitos-trabalhistas','Em 2022, seu mandato registrou apoio ao piso da enfermagem.','Artigo autoral de 05/05/2022: atribuir ao mandato; não equivale a auditoria nominal de votação.')])

candidate('240002533831', [
('c1','A','direitos-lgbtqia','Defende o enfrentamento à LGBTfobia.','Site / Nossas lutas: bandeira expressa.'),
('c1','A','direitos-mulheres','Defende respeito às mulheres e enfrentamento à violência de gênero.','Site / Nossas lutas; não importar alegações de resultados do bloco de leis.'),
('c1','A','direitos-trabalhistas','Defende o fim da escala de trabalho 6×1.','Site / Nossas lutas: posição atual explícita.'),
('c1','A','saude','Defende o SUS.','Site / Nossas lutas: defesa expressa; nomes isolados de localidades não geram outras tags.'),
('c2','A','direitos-mulheres','Defende a aplicação de políticas de proteção às mulheres.','Entrevista individual no PCdoB, 13/05/2026; não importar programa geral partidário.'),
('c2','A','direitos-trabalhistas','Defende oportunidades de trabalho digno para a juventude.','Entrevista / respostas sobre condições de trabalho: público específico.'),
('c2','A','educacao','Defende ampliar o acesso da juventude à educação.','Entrevista / respostas sobre juventude e educação: apoio expresso.'),
('c2','A','infancia-juventude','Defende acesso dos jovens à educação e ao trabalho digno.','Entrevista / juventude: ambas as frentes são expressas, sem inferência etária.')])

candidate('240002537831', [
('c1','A','cultura','Defende preservar e reutilizar a Antiga Rodoviária de Florianópolis como patrimônio de uso público.','Entrevista / Antiga Rodoviária: a defesa é retomada no presente, não apenas recordada como protesto passado.'),
('c1','A','moradia-cidades','Defende manter espaços e funções públicas no centro da cidade.','Entrevista / Antiga Rodoviária: delimitar o objeto urbano, sem inventar programa de habitação.'),
('c2','T','agua-saneamento','Relata ter produzido um vídeo sobre extravasamento de esgoto na Lagoa da Conceição.','Entrevista / relato anterior à audiência: ação de denúncia, não proposta de investimento em saneamento.'),
('c2','A','democracia-participacao','Defende a participação social por associações de bairro e organização comunitária.','Entrevista / resposta final: defesa atual da organização social; não inventar conselho ou instrumento de gestão.'),
('c2','T','meio-ambiente-clima servicos-publicos','Relata que cobrou estrutura, servidores e investimento para a política ambiental em uma audiência na Alesc.','Entrevista / relato do discurso na audiência: data da entrevista não data o evento; separar atuação de plataforma.')])

candidate('240002537839', [
('c1','A','direitos-trabalhistas','Defende o fim da escala de trabalho 6×1.','Legenda autoral do Instagram, antes dos comentários; sugestão tributária de terceiro não é posição da candidatura.')])

candidate('240002537832', [
('c1','A','democracia-participacao','Defende a participação popular nas decisões políticas.','QueroApoiar / apresentação em primeira pessoa: diálogo e participação são compromissos expressos.'),
('c1','P','educacao','Apresenta a educação pública como prioridade.','QueroApoiar / prioridades atuais: separar as mobilizações contra cortes de 2018–2019, narradas como trajetória.'),
('c2','P','cultura','Inclui a cultura entre suas prioridades.','QueroApoiar / apresentação: prioridade expressa, sem programa setorial completo presumido.'),
('c2','P','democracia-participacao','Inclui a defesa da democracia entre suas prioridades.','QueroApoiar / apresentação: posição declarada, não deduzida da filiação.'),
('c2','P','direitos-humanos','Inclui os direitos humanos entre suas prioridades.','QueroApoiar / apresentação: expressão nominal, não qualquer menção genérica a direitos.'),
('c2','P','direitos-lgbtqia','Inclui os direitos LGBTQIA+ entre suas prioridades.','QueroApoiar / prioridades: manifesto, não atributo pessoal.'),
('c2','P','infancia-juventude','Inclui a juventude entre suas prioridades.','QueroApoiar / apresentação: público expresso, não ampliar para política de infância não mencionada.'),
('c2','P','meio-ambiente-clima','Inclui o meio ambiente entre suas prioridades.','QueroApoiar / temas declarados: não inferir toda política climática.'),
('c2','P','saude','Inclui a saúde pública e o SUS entre suas prioridades.','QueroApoiar / temas declarados: SUS aparece explicitamente.')])

candidate('240002537838', [
('c1','A','democracia-participacao','Defende a democracia.','Site / eixos e bandeiras: compromisso político expresso.'),
('c1','A','direitos-lgbtqia','Defende os direitos da população LGBTQIA+.','Site / feminismo e direitos: não usar orientação ou identidade pessoal como evidência.'),
('c1','A','direitos-mulheres','Defende os direitos das mulheres e políticas feministas.','Site / bandeiras: declaração própria, sem extensão automática a toda medida.'),
('c1','A','liberdade-expressao','Defende a liberdade de expressão.','Site / democracia e comunicação: defesa expressa; regulamentação digital requer objeto separado.'),
('c2','P','agricultura-agroecologia','Defende o incentivo à agroecologia.','Site / eixo ambiental e produção: agroecologia expressa, não presumida pela defesa da natureza.'),
('c2','P','cultura','Defende a cultura popular.','Site / cultura e comunicação: prioridade declarada.'),
('c2','P','direitos-trabalhistas','Defende condições dignas de trabalho.','Site / trabalho: prioridade explícita, sem atribuir toda medida de jornada.'),
('c2','P','liberdade-expressao','Defende uma comunicação livre.','Site / comunicação: compromisso próprio; não importar conteúdos de terceiros.'),
('c2','P','meio-ambiente-clima','Defende justiça climática.','Site / eixo ambiental: bandeira expressa.'),
('c2','P','saude','Defende o fortalecimento da saúde pública.','Site / saúde: posição expressa; temas novos encontrados entram em fila separada, não por automatismo.')])

candidate('240002537830', [
('c1','H','direitos-lgbtqia educacao','Em 2023, defendeu políticas de acesso e permanência de pessoas trans e travestis na universidade e enfrentamento à transfobia.','Apufsc, 09/08/2023: usar somente falas atribuídas a Mirê; não transferir falas de outras participantes nem confirmar pauta atual.')])

candidate('240002537841', [
('c1','A','cultura','Defende a criação de um Museu dos Povos Originários em Santa Catarina.','Site / O que leva para o Congresso: pauta iniciada em 2018 é explicitamente reafirmada na apresentação atual.'),
('c1','A','povos-indigenas-tradicionais','Defende reconhecer e proteger territórios indígenas e quilombolas.','Site / Reforma Agrária Popular e territórios: proposta expressa, não inferência pela identidade.'),
('c1','A','saude','Defende ampliar orçamento e equipes da saúde indígena por meio da Sesai.','Site / Funai e Sesai fortalecidas: finalidade de saúde explicitada.'),
('c1','A','servicos-publicos','Defende orçamento, equipes e valorização dos servidores da Funai e da Sesai.','Site / Funai e Sesai fortalecidas: capacidade institucional, não apenas saúde genérica.'),
('c2','A','agricultura-agroecologia','Defende agricultura familiar, reforma agrária e agroecologia, com assistência técnica, crédito e comercialização.','Site / três projetos rurais: medidas e públicos expressos, sem equiparar toda agricultura à agroecologia.'),
('c3','P','direitos-mulheres','Defende atendimento às mulheres e enfrentamento ao feminicídio.','Site / Bandeiras de luta: Casa da Mulher Brasileira em SC e enfrentamento ao feminicídio.'),
('c3','P','meio-ambiente-clima','Apresenta a justiça climática entre suas bandeiras.','Site / Bandeiras de luta: compromisso atual expresso.'),
('c3','P','moradia-cidades','Apresenta a moradia popular entre suas bandeiras.','Site / Bandeiras de luta: prioridade expressa, sem inventar instrumentos habitacionais.'),
('c3','P','pessoas-deficiencia','Defende acessibilidade para pessoas com deficiência.','Site / Bandeiras de luta: público explicitamente nomeado, não deduzido da palavra acessibilidade.'),
('c3','P','pessoas-idosas','Defende acessibilidade para pessoas idosas.','Site / Bandeiras de luta: pessoas idosas citadas expressamente.'),
('c3','P','saude','Apresenta a cannabis medicinal entre suas bandeiras.','Site / Bandeiras de luta: tema expresso; não são feitas afirmações médicas de eficácia.')])

candidate('240002537836', [
('c1','A','democracia-participacao','Defende ampliar o diálogo do planejamento urbano com moradores, movimentos sociais, universidades e técnicos públicos.','Carta de 06/04/2026 / convite final: participação defendida no presente.'),
('c1','A','moradia-cidades','Defende um planejamento comprometido com o direito à cidade, a inclusão social e a dimensão metropolitana.','Carta / conclusão e crítica ao recorte territorial: preservar o escopo urbano, não criar um programa federal integral.'),
('c2','C','moradia-cidades','Critica a concentração territorial de investimentos e alerta para o risco de expulsão de moradores.','Carta / itens 3 e 4: diagnóstico crítico, não proposta orçamentária específica para periferias.')])

candidate('240002533820', [
('c1','H','moradia-cidades','A revisão anterior registrou pedidos municipais de pavimentação e de alteração de tampas de drenagem apresentados em 2023.','Ata 08/02/2023, indicações 37, 38, 39 e 44: fonte indisponível na reconferência; conservar proveniência sem afirmar nova validação.')])

candidate('240002543042', [
('c1','A','direitos-mulheres','Defende identificar precocemente a violência psicológica e patrimonial e integrar a rede de proteção às mulheres.','Lance Notícias / declarações da candidata e Chegar antes: medidas expressas, não estatísticas de terceiros.'),
('c1','A','seguranca-politica-penal','Defende mais recursos para atendimento e medidas protetivas às vítimas.','Lance Notícias / rede de proteção: objeto delimitado, não política penal genérica.'),
('c2','A','cuidado-protecao-social','Defende assistência jurídica e acolhimento para vítimas de violência.','Lance Notícias / Chegar antes: serviços de proteção expressos.'),
('c2','A','direitos-mulheres','Defende qualificação profissional e autonomia econômica para mulheres vítimas de violência.','Lance Notícias / Chegar antes: público e medidas explicitados.'),
('c2','A','seguranca-politica-penal','Propõe dados sobre violência e ações para reduzir a reincidência dos agressores.','Lance Notícias / medidas de prevenção: sem adotar números estatísticos não verificados.')])

candidate('240002541412', [
('c1','U','educacao infancia-juventude','A apresentação individual relata atuação por investimento na educação pública e condições de acesso e permanência de jovens trabalhadores.','UP / Conheça a trajetória: período da apresentação não confirmado; relato de mobilização não vira plataforma de 2026.')])

candidate('240002539586', [
('c1','U','direitos-trabalhistas','A apresentação individual defende direitos dos trabalhadores e combate aos baixos salários e ao custo de vida.','UP / apresentação individual sem data original: apoio registrado, mas atualidade não confirmada.'),
('c1','U','moradia-cidades','A apresentação individual defende reforma urbana e maior acesso à cidade.','UP / apresentação individual sem período: não datar pela consulta nem atribuir automaticamente a 2026.')])

candidate('240002553721', [
('c1','U','empresas-publicas-privatizacoes','Na apresentação consultada, defende reverter privatizações e reestatizar empresas.','PCO / página individual: posição expressa, período indeterminado; não excluir a família do catálogo.'),
('c1','U','politica-internacional','Na apresentação consultada, declara uma orientação anti-imperialista.','PCO / página individual: autodefinição sem período; não inferir apoio a todo governo ou conflito.')])

candidate('240002553720', [
('c1','U','direitos-trabalhistas','Na apresentação consultada, defende semana de trabalho de 35 horas.','PCO / página individual: medida expressa, período não confirmado.'),
('c1','U','educacao','Na apresentação consultada, defende ingresso universitário sem vestibular.','PCO / página individual: medida expressa; não declarar programa de 2026 sem confirmação temporal.'),
('c1','U','mobilidade-transporte','Na apresentação consultada, defende transporte gratuito para desempregados e trabalhadores informais.','PCO / página individual: gratuidade limitada aos públicos citados, não tarifa zero universal.'),
('c2','U','liberdade-expressao','Na apresentação consultada, defende liberdade de expressão e se opõe à censura.','PCO / página individual sem período: não deduzir posição sobre toda regulação digital.'),
('c2','U','politica-internacional','Na apresentação consultada, declara apoio a povos que identifica como resistentes ao imperialismo.','PCO / página individual: conservar atribuição, sem transferir apoio a governos ou organizações; período indeterminado.')])

candidate('240002533829', [
('c1','T','saude educacao infraestrutura-desenvolvimento','Relata uma reunião na qual discutiu investimentos em saúde, educação e infraestrutura para Balneário Camboriú e região.','Legenda autoral: descreve encontro passado e intenção genérica de ampliar a atuação; não detalha novo compromisso setorial para cada tema.')])

candidate('240002533838', [
('c1','A','educacao','Declara compromisso com a educação pública.','Legenda autoral do Instagram: compromisso expresso, não apenas biografia de professora.'),
('c1','A','democracia-participacao','Defende a participação da população nas decisões políticas.','Legenda autoral: compromisso expresso; trabalhar anteriormente em escala 6×1 não é posição sobre sua extinção.')])

candidate('240002537826', [
('c1','P','cuidado-protecao-social','A coletiva apresenta o cuidado como prioridade política.','Legenda de lutamadre / Coletiva SC Plural identificada por nome e número: autoria da própria coletiva, não atribuição externa.'),
('c1','A','direitos-mulheres democracia-participacao','A coletiva defende maior participação de mulheres e mães nos espaços de decisão.','Legenda autoral: compromisso afirmativo; não deduzir medidas de creches ou licenças ausentes do texto.')])

candidate('240002537827', [
('c1','A','direitos-trabalhistas','Defende o fim da escala 6×1, jornada de 40 horas, dois dias de descanso e manutenção salarial.','Facebook / legenda do vídeo principal: não usar vídeos relacionados nem confirmar calendário legislativo pela postagem.'),
('c2','A','educacao igualdade-racial','Defende a manutenção das cotas raciais nas universidades de Santa Catarina.','Facebook / legenda do vídeo individual sobre cotas: posição própria, não inferida pela identidade.')])

candidate('240002537840', [
('c1','J','educacao direitos-trabalhistas liberdade-expressao','Uma publicação conjunta de campanha o apresenta como defensor de educação plural, valorização docente e liberdade pedagógica.','Legenda publicada por Leonel Camasão e atribuída também a Thiago Moreti; não há declaração individual transcrita validada nesta revisão.')])

candidate('240002537833', [
('c1','A','direitos-trabalhistas','Defende o fim da escala 6×1 e direitos dos trabalhadores por aplicativo.','Instagram / legenda autoral de propostas: duas medidas trabalhistas expressas.'),
('c1','A','mobilidade-transporte','Defende tarifa zero no transporte público.','Instagram / legenda de propostas: gratuidade expressa.'),
('c2','A','saude','Defende ampliar os investimentos em saúde.','Instagram / legenda de propostas: prioridade de financiamento; não equivale a posição sobre toda medida do SUS.'),
('c2','A','educacao','Defende ampliar os investimentos em educação.','Instagram / legenda de propostas: compromisso expresso, não mera referência biográfica.'),
('c2','O','apostas-jogos','Defende combater as bets e os jogos de azar.','Instagram / legenda de propostas: conservar oposição à atividade, sem apresentar apoio a jogos.')])

EXTRA_CONTEXT = {
'240002533824': [('c3','historico','O site também relata voto pelo fim da escala 6×1; a votação nominal não foi reconferida nesta auditoria.','240002533824-s1')],
'240002537832': [('c1','historico','Sua apresentação relata mobilizações estudantis contra cortes na educação em 2018–2019.','240002537832-s1')],
'240002533830': [('c1','posicoes','Declara oposição ao Marco Temporal.','240002533830-s1')],
'240002533829': [('c1','posicoes','Apresenta a intenção de levar a experiência de sua atuação municipal para Brasília.','240002533829-s1')]
}

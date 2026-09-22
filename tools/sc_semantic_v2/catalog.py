"""Camada de navegação proposta; preserva integralmente o catálogo documental v1.
Não habilita filtros. O agrupamento não atribui nenhum tema a uma candidatura.
"""
MACROS = [
('agricultura-campo','Agricultura e campo','agricultura-agroecologia','Produção rural, agricultura familiar e políticas agrárias; o detalhe distingue agroecologia de outras medidas.'),
('cidades-infraestrutura','Cidades e infraestrutura','agua-saneamento mobilidade-transporte moradia-cidades infraestrutura-desenvolvimento','Habitação, transporte, água, saneamento e infraestrutura territorial, sem presumir que apoio a uma frente implique todas.'),
('cultura','Cultura','cultura','Preservar uma entrada própria para artes, memória e patrimônio; relações internacionais não são fundidas com cultura.'),
('democracia-liberdades','Democracia e liberdades','democracia-participacao liberdade-expressao','Participação, transparência, democracia e comunicação livre; o objeto de cada posição continua explícito.'),
('direitos-igualdade','Direitos e igualdade','direitos-humanos direitos-lgbtqia igualdade-racial pessoas-deficiencia pessoas-idosas','Direitos humanos, LGBTQIA+, igualdade racial, deficiência e envelhecimento continuam visíveis na descrição e na ficha.'),
('economia-estado','Economia e Estado','tributacao empresas-publicas-privatizacoes servicos-publicos apostas-jogos','Impostos, empresas e serviços públicos e regulação de atividades econômicas. Apostas permanecem como assunto, não como atividade apoiada.'),
('educacao-infancia-juventude','Educação, infância e juventude','educacao infancia-juventude','Mantém educação e direitos de crianças e jovens na navegação; uma medida para crianças não implica posição sobre educação.'),
('ambiente-animais','Meio ambiente e proteção animal','meio-ambiente-clima prevencao-desastres protecao-animal','Clima, prevenção de desastres e proteção animal não desaparecem; animais têm nome explícito no rótulo público.'),
('mulheres-cuidado','Mulheres e cuidado','direitos-mulheres cuidado-protecao-social','Direitos das mulheres e políticas de cuidado e assistência; cuidado não se restringe a mulheres nem implica proposta de creche.'),
('povos-territorios','Povos e territórios','povos-indigenas-tradicionais','Povos indígenas, quilombolas e comunidades tradicionais preservam entrada própria e públicos específicos.'),
('relacoes-internacionais','Relações internacionais','politica-internacional','Tema preservado em grupo próprio mesmo sem apoio atual elegível; não criar um botão com correspondências inventadas.'),
('saude','Saúde','saude','Tema amplo; SUS, atenção básica, saúde indígena e outras medidas só constam quando explicitamente documentadas.'),
('seguranca-justica','Segurança e justiça','seguranca-politica-penal','Segurança, proteção e justiça; preservar oposição ou apoio à medida concreta, sem atribuir uma política penal inteira.'),
('trabalho-renda','Trabalho e renda','direitos-trabalhistas','Jornada, remuneração, direitos e condições de trabalho; não inferir renda ou direitos só pela profissão da pessoa.')
]

FAMILY_NOTES = {
'agricultura-agroecologia':'Não confundir origem rural, agronegócio e agroecologia. Reafirmação atual é necessária para o registro agroflorestal histórico de Uczai.',
'agua-saneamento':'Restauração de rios não é automaticamente saneamento. A denúncia de esgoto por Drag Urbana é atuação, não um programa de investimento.',
'apostas-jogos':'As evidências deste recorte são de combate/oposição. O tema fica no grupo econômico e em Posições públicas, não em apoio a apostas.',
'cuidado-protecao-social':'Defesa expressa de cuidado ou acolhimento é suficiente; maternidade na biografia, por si só, não cria associação.',
'cultura':'Patrimônio e cultura popular cabem aqui. Não usar a profissão artística como pauta nem juntar política internacional para reduzir artificialmente o número de grupos.',
'democracia-participacao':'Distinguir defesa de participação na vida pública, convocação de evento e convite para apoiar uma campanha. Os três não são intercambiáveis.',
'direitos-mulheres':'Direitos e proteção precisam ser manifestados. Relatos de autoria de leis ficam separados de propostas atuais e de resultados comprovados.',
'direitos-humanos':'Exige declaração identificável; não é um rótulo automático para toda frase com justiça ou direitos.',
'direitos-lgbtqia':'Só posições expressas; identidade pessoal nunca é atalho. O histórico universitário de Mirê continua identificado como histórico.',
'direitos-trabalhistas':'Valorização salarial e jornada exigem objeto explícito. Separar voto relatado sobre 6×1 de defesa atual do salário mínimo.',
'educacao':'Prioridade ampla expressa é válida. Ser docente, ter participado de greve ou requerer um seminário não basta para uma pauta atual de campanha.',
'empresas-publicas-privatizacoes':'Mantida no catálogo e grupo econômico. O material individual sem período confirmado não entra por mera semelhança com a defesa de serviços públicos.',
'igualdade-racial':'Cotas e antirracismo explicitados, não raça ou origem da candidatura. Uma associação pode alcançar também educação se a medida realmente tratar dos dois.',
'infancia-juventude':'Preservar públicos: uma defesa da juventude não atribui automaticamente uma política de primeira infância. O rótulo amplo não substitui essa distinção.',
'infraestrutura-desenvolvimento':'Não converter tema de reunião passada em novo compromisso de investimento. A família permanece mesmo sem associação atual elegível após revisão.',
'liberdade-expressao':'Manter oposição à censura e defesa de comunicação sem inferir adesão a toda proposta de regulação digital.',
'meio-ambiente-clima':'Não transformar autodescrição de atuação ambiental em programa. Declarações atuais de conservação ou justiça climática permanecem suficientes.',
'mobilidade-transporte':'Distinguir transporte, gratuidade focalizada e tarifa zero universal. O macrogrupo não elimina o objeto concreto.',
'moradia-cidades':'Distinguir direito à cidade e uso público de patrimônio de crítica a projeto urbanístico ou de uma política habitacional inventada.',
'pessoas-deficiencia':'Em Nandja o público está explicitado na fonte. Acessibilidade genérica e a palavra deficiência em outro contexto não bastam.',
'pessoas-idosas':'Envelhecimento está expresso em Caren, Lirous e Nandja; não derivar a pauta da idade da candidatura ou de cuidado genérico.',
'politica-internacional':'Preservada em grupo próprio; posição/autodefinição sem período permanece em contexto. Nunca presumir apoio a governos ou organizações.',
'povos-indigenas-tradicionais':'Manter povos, demarcação e territórios sem usar identidade indígena como evidência nem reduzir tudo a política rural.',
'prevencao-desastres':'Declaração atual de prevenção é válida; descrição de atuação anterior não basta. Não inferir desastres a partir de qualquer menção ao clima.',
'protecao-animal':'Mantida e nomeada no macrogrupo ambiental. Defesa expressa é necessária, não fotografia com animais ou profissão.',
'saude':'Saúde permanece ampla. Menção a investimento não comprova apoio específico ao SUS, cannabis, enfermagem ou estatuto de transplantados.',
'seguranca-politica-penal':'Efetivo, formação, medidas protetivas e armas são objetos distintos. A posição sobre um deles não demonstra orientação penal integral.',
'servicos-publicos':'Exige defesa explícita de capacidade ou serviço público; não adicionar automaticamente a toda menção a educação e saúde.',
'tributacao':'A entrevista de Jú sustenta política de impostos sobre renda e patrimônio. Declaração de bens, regularidade fiscal ou palavra solta não são pautas tributárias.'
}

EXTENSION_QUEUE = [
{'area':'Ciência, tecnologia e inovação','status':'indicio_documental_para_revisao','source_ids':['240002537838-s1','240002533830-s1'],'note':'As páginas trazem referências programáticas a ciência. Requer nova associação individual e definição de família; não foi ativada neste round.'},
{'area':'Comunicação e política digital','status':'indicio_documental_para_revisao','source_ids':['240002537838-s1'],'note':'Há posição sobre big techs e comunicação. Liberdade de expressão não cobre automaticamente toda política digital; rever antes de ampliar o catálogo.'},
{'area':'Previdência','status':'lacuna_de_catalogo_a_avaliar','source_ids':[],'note':'Não há associação individual aprovada nesta matriz. Isso não demonstra ausência de posição nas candidaturas.'},
{'area':'Esporte e lazer','status':'lacuna_de_catalogo_a_avaliar','source_ids':[],'note':'A auditoria não fez um novo levantamento exaustivo de programas; avaliar em nova pesquisa, sem preencher por inferência.'},
{'area':'Energia','status':'lacuna_de_catalogo_a_avaliar','source_ids':[],'note':'Não atribuir automaticamente toda política energética a quem fala de clima; precisa de revisão individual do objeto.'},
{'area':'Direitos do consumidor','status':'lacuna_de_catalogo_a_avaliar','source_ids':[],'note':'Combate a apostas ou referência a custo de vida não gera uma defesa genérica de todos os direitos do consumidor.'}
]

POLICY = {
'version':'2.0.0-round1',
'ui_active':False,
'groups_are_navigation_only':True,
'group_count_target':'aproximadamente 12–14; não exige 14 botões se um grupo tiver zero correspondência',
'one_primary_group_per_family':True,
'broad_priority':'Prioridade ampla explicitamente declarada é válida. Não exigir projeto de lei ou mecanismo detalhado para Saúde, Educação ou outro eixo amplo.',
'currentness':'A data da fonte, a data do ato e a reafirmação atual são campos distintos. Um projeto antigo pode ser pauta atual se houver reafirmação expressa.',
'undated':'Sem período não é sinônimo de histórico. Conservar em contexto documental, sem inventar atualidade ou antiguidade.',
'opposition':'Oposição pode ser uma posição política substantiva; sua exclusão deste filtro positivo é uma escolha de recorte, não um juízo de mérito nem ausência de pauta. Não reescrever oposição como apoio à atividade.',
'no_inference':'O grupo só recebe a união das associações individuais aprovadas; não propaga apoio às famílias irmãs.',
'and':'Todas exige ao menos uma associação elegível por macrogrupo; evidência de uma família não passa automaticamente para outro grupo.',
'coverage':'Contagens são pessoas distintas, não afirmações. Listas vazias não significam oposição.',
'round2':'Usar candidate-content.json e association-audit.json em conjunto; nunca reutilizar silenciosamente a elegibilidade v1.',
'future':'As 29 famílias não são um inventário exaustivo de políticas públicas. A fila de extensão não cria tags nem novas associações.'
}

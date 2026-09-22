"""Hand-reviewed vocabulary decisions for #53. These are NOT candidate labels.
The source catalogues are pinned and audited separately by build.py.
A related concept keeps its original scope; no graph traversal creates evidence.
"""
BASE = '60f4d533d55e07f5a56847adb09a8a88fec37938'
VERSION = '1.0.0'
# New domains contributed by RS and PR; science is imported from SP's definition.
EXTENSIONS = [
 ('direitos-consumidor','Direitos do consumidor','Proteção nas relações de consumo, defesa do consumidor e práticas comerciais documentadas.','Não transformar toda proposta de renda, tributação ou regulação de apostas em defesa do consumidor.','rs-v1:consumidor'),
 ('esporte-lazer','Esporte e lazer','Acesso, políticas e equipamentos de esporte e lazer explicitados.','Profissão esportiva, patrocínio ou presença em evento não bastam.','rs-v1:esporte'),
 ('liberdade-religiosa','Liberdade religiosa','Liberdade de crença, culto, consciência e enfrentamento à intolerância religiosa quando explicitados.','Religião, identidade da candidatura ou liberdade de expressão genérica não comprovam esta pauta.','rs-v1:liberdade-religiosa'),
 ('previdencia','Previdência','Direitos, regras, financiamento e benefícios previdenciários explicitados.','Não confundir aposentadoria com toda proteção social nem presumir posição sobre uma reforma específica.','rs-v1:previdencia'),
 ('direitos-sociais','Direitos sociais','Referência expressa a direitos sociais, preservando o direito e o objeto enunciados.','Não distribuir automaticamente esta rubrica ampla para saúde, moradia, trabalho ou direitos humanos.','rs-v1:direitos-sociais'),
 ('trabalho-renda','Trabalho, emprego e renda','Trabalho, geração de emprego, ocupação e renda expressamente documentados.','Não inferir defesa de direitos trabalhistas, de uma jornada ou de transferência de renda específica.','rs-v1:trabalho'),
 ('desenvolvimento-industria','Desenvolvimento regional e indústria','Políticas de desenvolvimento regional e industrial explicitadas, com objeto e localidade preservados.','Não converter desenvolvimento em promessa de obra nem indústria em apoio a qualquer política ambiental.','rs-v1:desenvolvimento-regional'),
 ('renda-protecao-social','Renda e proteção social','Medidas de renda, transferência e proteção social expressamente documentadas.','Não inferir política de cuidados, previdência ou direitos trabalhistas apenas por proximidade temática.','pr-v1:renda'),
 ('seguranca-alimentar','Segurança alimentar','Acesso a alimentos, combate à fome, alimentação e segurança alimentar explicitados.','Não inferir agroecologia, reforma agrária ou origem da produção a partir do objetivo de combater a fome.','pr-v1:seguranca-alimentar'),
]
# source-id | canonical-id | relation | set relation | rationale.
# Label-only catalogues deliberately receive bounded links, not exactMatch.
RS = '''agricultura-familiar|agricultura-agroecologia|related|narrower|A rubrica RS junta agricultura familiar e agroecologia; preservar qual prática a fonte menciona, sem adicionar reforma agrária.
ciencia-tecnologia|ciencia-tecnologia-inovacao|related|narrower|Ciência e tecnologia se encaixam no domínio; inovação não é atribuída sem objeto expresso.
consumidor|direitos-consumidor|specific|same|Extensão do RS preservada como domínio próprio; não havia correspondente explícito em SC.
cultura|cultura|related|bounded_label|Mesmo assunto nominal, mas RS não define inclusões/exclusões; conservar o vínculo documental original.
desenvolvimento-regional|desenvolvimento-industria|specific|same|A indústria explícita na rubrica RS não deve desaparecer dentro de infraestrutura.
direitos-lgbtqia|direitos-lgbtqia|related|bounded_label|O público coincide; não inferir identidade ou medida específica da candidatura.
direitos-mulheres|direitos-mulheres|related|bounded_label|Mesmo público nominal; a fonte individual continua delimitando direitos e medidas.
direitos-sociais|direitos-sociais|specific|same|Rubrica ampla do RS conservada, sem distribuição para todos os direitos setoriais.
educacao|educacao|related|bounded_label|Domínio educacional comum; não inferir rede, nível ou modalidade sem fonte.
esporte|esporte-lazer|specific|same|Extensão RS com esporte e lazer explicitamente presentes no catálogo.
igualdade-racial|igualdade-racial|related|bounded_label|Mesmo domínio nominal; raça da pessoa não participa do mapeamento.
infancia-adolescencia|infancia-juventude|related|narrower|Crianças e adolescentes são recorte mais estreito; não atribuir políticas para jovens adultos.
liberdade-religiosa|liberdade-religiosa|specific|same|Domínio próprio do RS; não equivale a toda liberdade civil ou à religião da pessoa.
meio-ambiente|meio-ambiente-clima|related|bounded_label|O rótulo RS inclui clima, mas cada evidência pode tratar apenas de um objeto ambiental.
mobilidade|mobilidade-transporte|related|bounded_label|O rótulo inclui transporte; tarifa zero e outras medidas exigem objeto próprio.
moradia|moradia-cidades|related|overlap|Regularização fundiária pode ter escopo distinto de urbanismo; decisão por afirmação antes de transportar esse vínculo.
pessoas-com-deficiencia|pessoas-deficiencia|related|bounded_label|Mesmo público nominal, com medida e fonte preservadas; não se confunde com ciência.
pessoas-idosas|pessoas-idosas|related|bounded_label|Mesmo público nominal; não inferir previdência a partir de idade ou tema.
povos-tradicionais|povos-indigenas-tradicionais|related|bounded_label|O catálogo RS menciona indígenas e comunidades tradicionais; não propagar associação entre povos.
previdencia|previdencia|specific|same|Extensão RS independente de proteção social genérica e tributação.
protecao-animal|protecao-animal|related|bounded_label|Mesmo domínio nominal; a fonte deve apontar defesa, ato ou contexto específico.
reforma-agraria|agricultura-agroecologia|related|narrower|Reforma agrária é um objeto possível do domínio agrário, não consequência de todo apoio à agricultura.
saneamento|agua-saneamento|related|narrower|Saneamento não implica todo abastecimento/acesso à água; manter o recorte original.
saude|saude|related|bounded_label|Saúde é o domínio comum; não acrescentar SUS, cannabis, enfermagem ou modalidade de cuidado.
seguranca-publica|seguranca-politica-penal|related|narrower|Segurança pública não estabelece posição sobre armas, penas ou maioridade penal.
servico-publico|servicos-publicos|related|bounded_label|Domínio de serviço público comum; não inferir posição sobre propriedade de empresas.
trabalho|trabalho-renda|specific|same|O rótulo RS inclui renda e não só direitos trabalhistas; conservar domínio abrangente próprio.
tributacao|tributacao|related|bounded_label|Mesmo assunto nominal; sujeito, imposto e direção precisam continuar explícitos.'''
PR = '''educacao|educacao|related|narrower|O rótulo PR restringe à educação pública; não presumir todos os níveis ou modalidades.
saude|saude|related|narrower|A rubrica PR menciona SUS, mas o objeto da fonte delimita cada associação; não propagar apoio específico pelo rótulo.
trabalho|direitos-trabalhistas|related|overlap|Trabalho e direitos trabalhistas podem conter geração de emprego; exigir objeto antes de classificar como defesa de direitos.
renda|renda-protecao-social|specific|same|Preservar renda e proteção social, sem absorver automaticamente em cuidado ou previdência.
moradia|moradia-cidades|related|narrower|Moradia é recorte do domínio urbano; não acrescentar saneamento, mobilidade ou reforma urbana.
mobilidade|mobilidade-transporte|related|bounded_label|Rótulo comum de mobilidade e transporte; conservar a medida efetivamente citada.
meio-ambiente|meio-ambiente-clima|related|bounded_label|Rótulo inclui ambiente e clima; não extrapolar um ato pontual para todo o domínio.
agricultura-familiar|agricultura-agroecologia|related|narrower|Agricultura familiar não equivale a agroecologia nem a reforma agrária; o recorte original fica visível.
reforma-agraria|agricultura-agroecologia|related|narrower|Reforma agrária é objeto específico, sem atribuição de outras práticas agrícolas.
seguranca-alimentar|seguranca-alimentar|specific|same|Extensão do PR independente de método de cultivo ou distribuição da terra.
mulheres|direitos-mulheres|related|bounded_label|Mesmo público no rótulo, não inferir aborto, programa ou posição não expressa.
igualdade-racial|igualdade-racial|related|bounded_label|Mesmo assunto nominal; a evidência é individual, não raça ou filiação.
lgbtqia|direitos-lgbtqia|related|bounded_label|Mesmo público nominal; manter a medida e não inferir identidade pessoal.
povos-indigenas|povos-indigenas-tradicionais|related|bounded_label|Apesar do ID estreito, o rótulo PR inclui comunidades tradicionais; preservar o público da fonte.
pessoa-deficiencia|pessoas-deficiencia|related|bounded_label|Variação nominal singular/plural; a medida acessível continua limitada à fonte.
cultura|cultura|related|bounded_label|Mesmo assunto nominal sem definição extensa PR; o vínculo documental limita a leitura.
ciencia-tecnologia|ciencia-tecnologia-inovacao|related|narrower|Ciência e tecnologia não implicam compromisso adicional com inovação específica.
juventude|infancia-juventude|related|narrower|Juventude não cria associação a crianças, creches ou adolescência.
seguranca-publica|seguranca-politica-penal|related|narrower|Recorte de segurança pública não estabelece toda uma política penal.
direitos-humanos|direitos-humanos|related|bounded_label|Preservar expressão atribuída e fonte; não distribuir automaticamente a todo direito social.
servicos-publicos|servicos-publicos|related|bounded_label|Mesma rubrica nominal; serviços não equivalem a oposição à privatização.
democracia|democracia-participacao|related|bounded_label|O rótulo PR inclui participação; não inferir qualquer mecanismo institucional adicional.
tributacao|tributacao|related|bounded_label|A fonte deve identificar imposto, incidência ou direção; não deduzir da desigualdade.
saneamento|agua-saneamento|related|bounded_label|O rótulo PR contém água e saneamento, mas não dispensa preservar o objeto da evidência.
protecao-animal|protecao-animal|related|bounded_label|Mesmo assunto nominal; nome, profissão ou foto não entram no critério.'''
# Explicitly rejected shortcuts (not candidate classifications).
REJECTED = [
 ('rs-v1:trabalho','direitos-trabalhistas','not_comparable','Trabalho e renda não são equivalentes a direitos trabalhistas; renda/emprego podem ter outro objeto.'),
 ('rs-v1:direitos-sociais','direitos-humanos','not_comparable','Não substituir rubrica social ampla por direitos humanos nem por todas as suas políticas possíveis.'),
 ('rs-v1:liberdade-religiosa','liberdade-expressao','not_comparable','Liberdade religiosa é preservada como domínio próprio; proximidade não significa equivalência.'),
 ('pr-v1:seguranca-alimentar','agricultura-agroecologia','not_comparable','Combater a fome não comprova apoio à agroecologia ou à reforma agrária.'),
 ('rs-v1:desenvolvimento-regional','infraestrutura-desenvolvimento','review_required','A indústria e uma obra podem coincidir numa fonte; ligação depende do objeto, não só de desenvolvimento.'),
 ('pr-v1:trabalho','trabalho-renda','review_required','Distinguir geração de trabalho/renda de direito trabalhista por afirmação antes de dividir esta rubrica.'),
 ('rs-v1:moradia','agricultura-agroecologia','review_required','Regularização rural e moradia urbana não são intercambiáveis; a fonte define a abrangência.'),
 ('sp-product-v1:pessoas-deficiencia','ciencia-tecnologia-inovacao','not_comparable','Deficiência não é sinônimo de ciência; associação cruzada exige outra evidência, nunca esta conversão.'),
]
# Same global hierarchy everywhere, not a hierarchy of candidate relevance.
GROUPS = [
 ('agricultura-alimentacao','Agricultura e alimentação',['agricultura-agroecologia','seguranca-alimentar']),
 ('cidades-infraestrutura','Cidades e infraestrutura',['agua-saneamento','mobilidade-transporte','moradia-cidades','infraestrutura-desenvolvimento']),
 ('ciencia-tecnologia','Ciência e tecnologia',['ciencia-tecnologia-inovacao']),
 ('cultura-esporte','Cultura, esporte e lazer',['cultura','esporte-lazer']),
 ('democracia-liberdades','Democracia e liberdades',['democracia-participacao','liberdade-expressao','liberdade-religiosa']),
 ('direitos-igualdade','Direitos e igualdade',['direitos-humanos','direitos-lgbtqia','igualdade-racial','pessoas-deficiencia','pessoas-idosas','direitos-sociais']),
 ('economia-estado','Economia e Estado',['tributacao','empresas-publicas-privatizacoes','servicos-publicos','apostas-jogos','direitos-consumidor','desenvolvimento-industria']),
 ('educacao-geracoes','Educação, infância e juventude',['educacao','infancia-juventude']),
 ('meio-ambiente','Meio ambiente e desastres',['meio-ambiente-clima','prevencao-desastres']),
 ('mulheres-cuidado','Mulheres e cuidado',['direitos-mulheres','cuidado-protecao-social']),
 ('povos-territorios','Povos e territórios',['povos-indigenas-tradicionais']),
 ('protecao-animal','Proteção animal',['protecao-animal']),
 ('saude','Saúde',['saude']),
 ('seguranca','Segurança e política penal',['seguranca-politica-penal']),
 ('trabalho-protecao','Trabalho, renda e previdência',['direitos-trabalhistas','trabalho-renda','previdencia','renda-protecao-social']),
 ('internacional','Política internacional',['politica-internacional']),
]
# Syntax dialects are not renamed silently in old links.
RUNTIMES = {
 '2026-sc-federais':('assets/pauta-filters-editorial.js','current_support',['any','all'],['daily']),
 '2026-sc-estaduais':('deputados-estaduais/ui/app.js',None,[],['daily']),
 '2026-rs-federais':('tools/rs/runtime.js',None,[],['daily']),
 '2026-pr-federais':('tools/pr/runtime.js','legacy_context',['all'],['daily']),
 '2026-pr-estaduais':('tools/pr/runtime.js','legacy_context',['all'],['daily']),
 '2026-sp-federais':('sp/deputados-federais/assets/app.js','documented_topic',['any','all'],['daily','alphabetical']),
}
DATASETS = {
 '2026-sc-federais':('data/sc-semantic-v2/candidate-content.json','candidates'),
 '2026-sc-estaduais':('deputados-estaduais/data/candidaturas.json','candidates'),
 '2026-rs-federais':('rs/deputados-federais/dados.json','candidates'),
 '2026-pr-federais':('pr/deputados-federais/dados.json','candidates'),
 '2026-pr-estaduais':('pr/deputados-estaduais/dados.json','candidates'),
 '2026-sp-federais':('sp/deputados-federais/dados.json','records'),
}

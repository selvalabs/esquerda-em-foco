"""Reconferência editorial de fontes, não apenas HTTP. Sem cópias integrais de páginas.
W = leitura textual pública; R = leitura pública renderizada; X = não reconfirmada.
Data local de auditoria: 21/09/2026, America/Sao_Paulo. Execuções UTC avançam para 22/09.
"""
SOURCES = {
'240002541412-s1':('W','UP / Conheça a trajetória','Página individual sem data; relata mobilizações educacionais. Consulta atual não a transforma em plataforma de 2026.'),
'240002553721-s1':('W','PCO / apresentação individual de Ana Paula Adão','Posições individuais sobre privatizações e autodefinição internacional; período original não estabelecido.'),
'240002533824-s1':('W','Propósito; Trajetória Política; rodapé eleitoral','Contexto de 2026 explícito; distinguir verbos de defesa atual de autoria de projeto, relato de voto e descrição de atuação.'),
'240002543042-s1':('R','Lance Notícias / declarações e Chegar antes','Texto de 15/09/2026; legenda de foto histórica não data a proposta. Reproduz declarações da candidata, não valida seus números estatísticos.'),
'240002539586-s1':('W','UP / trajetória e apresentação de Andre Drejan','Posições individualizadas, mas data original e vinculação ao pleito atual não confirmadas.'),
'240002553720-s1':('W','PCO / texto individual de Arthur Cesconetto','Medidas individuais expressas; data original ausente. Preservar públicos da gratuidade e atribuição da posição internacional.'),
'240002533828-s1':('W','Apresentação; Pessoa Transplantada; referência a 2026','Ano do rodapé não prevalece sobre contexto atual no corpo. Prioridades amplas são expressas e válidas sem inventar instrumentos.'),
'240002533825-s1':('W','QueroApoiar / prioridades; Sou a favor; Sou contra','Candidatura individual e contexto eleitoral de 2026; listas positivas e negativas separadas.'),
'240002533825-s2':('W','Artigo autoral de 01/04/2026 sobre Casa da Mulher Brasileira','Confirma a defesa do atendimento integrado às mulheres; não transferir assuntos da barra lateral para a posição da autora.'),
'240002537831-s1':('W','Entrevista / audiência de esgoto; Antiga Rodoviária; resposta final','Publicada em 27/02/2026. Relatos retrospectivos de ações não viram propostas; defesa atual de patrimônio e organização comunitária permanece.'),
'240002533829-s1':('R','Legenda principal de eduardozanattabc, antes dos comentários','Nome e número correspondem; relata encontro e intenção de ampliar a atuação. Não formula compromisso setorial novo para cada assunto da reunião.'),
'240002537839-s1':('R','Legenda principal de gilsantos_vat','Confirma 6×1. O comentário tributário é de terceiro e não constitui manifestação da candidatura.'),
'240002533831-s1':('R','Nossas lutas; agenda 2026; bloco de leis separado','Defesas explícitas de 6×1, SUS, mulheres e enfrentamento à LGBTfobia. Não usar localidades isoladas, comentários de apoiadores ou teasers de imprensa.'),
'240002533831-s2':('W','Entrevista individual no PCdoB, 13/05/2026','Usar respostas de Giovana sobre mulheres, juventude, educação e trabalho, não diretrizes genéricas da legenda.'),
'240002537832-s1':('W','QueroApoiar / apresentação em primeira pessoa e prioridades','Manter prioridades atuais; separar mobilizações estudantis de 2018–2019 da defesa atual da educação.'),
'240002533820-s1':('X','Ata 08/02/2023; indicações 37, 38, 39 e 44 segundo a revisão anterior','Reabertura falhou, inclusive com HTTP 503; buscas complementares não permitiram reconferir. Manter registro histórico com ressalva, sem afirmar nova confirmação.'),
'240002537838-s1':('W','Site / eixos de bandeiras, cultura/comunicação e saúde','Defesas expressas; rodapé de template não data o programa. Referências a ciência e big techs são pistas para expansão futura, não associações automáticas.'),
'240002533832-s1':('W','Diário do Sul / Propostas; 16/09/2026, atualização 17/09/2026','Identifica Jucélia Vargas. Tributação é proposta de cobrança proporcional à renda e patrimônio, não regularidade fiscal ou declaração de bens.'),
'240002533826-s1':('W','QueroApoiar / apresentação; construção coletiva; convite final','Distinguir defesas de SUS, serviços, mulheres e trabalhadores de participação de apoiadores na construção da campanha.'),
'240002533830-s1':('W','Propostas / territórios, cuidado, mulheres e justiça climática','Atribuição individual; demarcação afirmativa e oposição ao Marco Temporal são preservadas separadamente.'),
'240002533827-s1':('R','VoteLGBT 2026 / Prioridades do mandato, ficha 99','Nome, número e cargo compatíveis. Usar prioridades declaradas, não os campos de identidade ou informações sensíveis do formulário.'),
'240002537826-s1':('R','Legenda principal de lutamadre / Coletiva SC Plural 5020','Autoria da própria candidatura coletiva identificada: cuidado e participação de mulheres/mães. Não inferir projetos de creche ou licença.'),
'240002537827-s1':('R','Facebook / legenda principal do vídeo de jornada','Posição sobre 6×1, 40 horas, descanso e salário. A legenda não serve para certificar calendário ou tramitação de PEC.'),
'240002537827-s2':('R','Facebook / legenda principal do vídeo sobre cotas','Apoio explícito às cotas raciais universitárias; vídeos relacionados não acrescentam pautas.'),
'240002537830-s1':('W','Apufsc, 09/08/2023 / falas atribuídas nominalmente a Mirê','Registro histórico; distinguir falas de outras participantes e não repetir estatísticas sem verificação própria.'),
'240002537841-s1':('R','O que leva para o Congresso; Bandeiras de luta','Museu antigo é reafirmado como pauta atual. Acessibilidade menciona expressamente deficiência e pessoas idosas.'),
'240002533838-s1':('R','Instagram / legenda principal de ju_andozio','Defesas de educação e participação explícitas; experiência biográfica em escala 6×1 não é apoio à sua extinção.'),
'240002533823-s1':('W','Alesc, 19/10/2023 / Causa negra como missão','Discurso histórico atribuído a Vanessa; não transformar notícia de posse em programa federal atual.'),
'240002537836-s1':('W','Carta reproduzida, 06/04/2026 / itens 3–4 e convite final','Separar diagnóstico crítico de distribuição territorial e gentrificação da defesa afirmativa de planejamento participativo; ignorar artigos relacionados embutidos.'),
'240002533833-s1':('W','Câmara / autoria, ementa e tramitação do REQ 23/2026 CE','Requerimento de seminário datado de 27/04/2026; aprovação do requerimento não é aprovação do PNE nem lei em vigor.'),
'240002533833-s2':('W','Edital de convocação Serramar / texto datado e publicação','Documento datado de 01/06, página de 02/06/2026. Convocação não prova que a assembleia ocorreu.'),
'240002533833-s3':('W','Manifestação autoral sobre bets, 09/07/2026','Posição contrária à atividade e favorável à intervenção/proibição; não é apoio a apostas.'),
'240002533833-s4':('W','Artigo sobre sistemas agroflorestais, 12/09/2023','Apoio ao fomento no PPA em contexto histórico; não presumir reafirmação atual.'),
'240002533833-s5':('W','Artigo do mandato sobre piso da enfermagem, 05/05/2022','Registro autoral histórico de apoio/voto; não equivale a confirmação independente de votação nominal.'),
'240002537840-s1':('R','Facebook / legenda do material conjunto de Leonel Camasão','Thiago Moreti é nominalmente identificado, mas a autoria é de outro participante; falta validação de declaração individual transcrita.'),
'240002537833-s1':('R','Instagram / legenda principal de victor_gaspodini','Lista de propostas e oposição às bets. Data relativa não convertida em dia exato; contexto eleitoral de 2026 preservado.')
}
RENDERED_HASHES = {
'240002543042-s1':'9a8f435b0c62b1198cdf90ce3b60e9e6e0b97a8054dcf6878d9cb072e3d6dfcb',
'240002533829-s1':'2818174c5653725ad8a3dbb95cdc270e6227e3b9ad903868867403d5b5672d4d',
'240002537839-s1':'72b08489f99fb453b1cad74ca2aea3d04387c9d22c6d645b0877b8320d44227c',
'240002533831-s1':'2c6ca00af69b9f7fbb7ad7a00af9295274c74e5cdfcbc4454c38fa626f215cab',
'240002533827-s1':'635a8cb5fce36ff53f8593c4a010e8f0fa311e92533adde22317210fdb4a6505',
'240002537826-s1':'2343c454ee49c3f8236d4e6a57d2fcfa2e34dfabfda376bf2f3fda92bb9d50a0',
'240002537827-s1':'be794585b3d5006bec8b84f072968286ef7e6854490aeaf6b1118ac72a15826a',
'240002537827-s2':'4db54e1c279a41b5562c20037be4ab73c315a5cc3a9522e9de007ae70bba8772',
'240002537841-s1':'add0deffe39fae5128658e786692f69b4978ef639db6794b7f1b4c76188ea9fc',
'240002533838-s1':'c50651bbb6df9e40debede9f622588920c47dc5edc6d5d1a46c91a7368f3df09',
'240002537840-s1':'698ff38e996e39d8d0caf4926f52adba1df8fe35599d2e4740772906cdee4da1',
'240002537833-s1':'feae56ab098c85ac498052e3b891bd4960918d1c57f06fbc545c63ea2042edf0'
}
RENDER_RUN = 'https://github.com/selvalabs/esquerda-em-foco/actions/runs/35674822480'
RENDER_ARTIFACT = 10672462600
RENDER_ZIP_SHA256 = '3caded4f41c481daa1a7e469669d40d9c8595288efb5c574b1a3008c0d063a20'

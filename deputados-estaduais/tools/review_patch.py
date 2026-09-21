"""One-time, idempotent corrections confined to state-front source files."""
from pathlib import Path
root=Path(__file__).resolve().parent
changes={
 'official.py': [
  ("if r['CD_CARGO']=='12': tickets[r['ANO_ELEICAO']].add((r['SG_UE'],r['NR_CANDIDATO'],r['NR_TURNO']))", "if r['CD_CARGO'] in ['4','12']: tickets[r['ANO_ELEICAO']].add((r['SG_UE'],r['NR_CANDIDATO'],r['NR_TURNO'],'3' if r['CD_CARGO']=='4' else '11'))"),
  ("ticket=cargo=='11' and (ue,nr,turn) in tickets[year]", "ticket=(ue,nr,turn,cargo) in tickets[year]")
 ],
 'render.py': [
  ("if r.get('CD_CARGO')=='12': key=", "if r.get('CD_CARGO') in ['4','12']: key="),
  ("if latest and latest['CD_CARGO']=='12':", "if latest and latest['CD_CARGO'] in ['4','12']:"),
  ("Na candidatura a vice-prefeito, a votação pertence à chapa.", "Na candidatura a vice, a votação pertence à chapa."),
  ("Para vice-prefeito, a votação é da chapa", "Para vice-prefeito ou vice-governador, a votação é da chapa"),
  ("A síntese de pautas individuais ainda não está consolidada nesta edição. Os canais declarados estão ao lado; posições gerais do partido não foram atribuídas automaticamente à candidatura.", "Pautas individuais ainda não consolidadas. Consulte os canais declarados; posições do partido não substituem um programa pessoal."),
  ("O histórico abaixo registra candidaturas e resultados. A ausência de confirmação nesta ficha não comprova ausência de mandato ou de atuação pública.", "Exercício atual não confirmado. O histórico registra disputas e resultados, não toda a atuação pública."),
  ("Sem mandato atual confirmado nesta edição", "Mandato atual não confirmado")
 ]
}
for name,pairs in changes.items():
 path=root/name; text=path.read_text(encoding='utf-8')
 for old,new in pairs:
  if old in text: text=text.replace(old,new)
  elif new not in text: raise ValueError('Review needed for '+name)
 path.write_text(text,encoding='utf-8')
print('State source corrections checked.')

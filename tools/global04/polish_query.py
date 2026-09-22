"""Final L02 lifecycle and verifier migration, idempotent and data-preserving."""
from finalize_query import edit,ROOT

def main():
    p='assets/global/query.js'
    edit(p,'adapter.applyState(parsed.state);lastState=copy(snapshot());sync();',"if(!same(parsed.state,snapshot())){\n      if(document.querySelector('article[data-eef-held]'))$('eefCollectionClose')?.click();\n      adapter.applyState(parsed.state);\n    }\n    lastState=copy(snapshot());sync();")
    edit(p,'if(entry){setState(entry.state);','if(entry){showNotice(\'\');setState(entry.state);')
    edit(p,'    sync();\n  }\n  function route(){','    if(!memoryEntry())remember();\n    sync();\n  }\n  function route(){')
    p='tests/global04/query_validate.py'
    edit(p," 'docs/GLOBAL-MIGRATION-PLAN.md'"," 'tools/sp/publication/verify_live.py','docs/GLOBAL-MIGRATION-PLAN.md'")
    p='tools/sp/publication/verify_live.py'
    edit(p,"assert 'partidos=PT' in page.url and 'pautas=saude' in page.url\n            page.reload(wait_until='domcontentloaded')", """if page.locator('#eefShareQuery').count():
                # New query choices are not automatically persisted in the address.
                assert not __import__('urllib.parse',fromlist=['urlsplit']).urlsplit(page.url).query
                page.locator('#eefShareQuery').click()
                shared=page.locator('#eefQueryShareUrl').input_value()
                assert '#eef=query&v=1&edition=2026-sp-federais&state=' in shared
                page.locator('#eefQueryShareClose').click()
                go(shared)
                count(expected)
            else:
                assert 'partidos=PT' in page.url and 'pautas=saude' in page.url
            page.reload(wait_until='domcontentloaded')""")
    p=ROOT/'docs/GLOBAL-04-LOTE02.md';s=p.read_text()
    extra='''
## Histórico, foco e privacidade nesta implementação

A History API recebe apenas uma chave opaca. As consultas correspondentes ficam
num Map em memória do documento, sem preferência em history.state, localStorage,
sessionStorage, cookie ou backend. Voltar/avançar pode restaurar etapas enquanto
esse documento existe. Recarga ou nova aba não promete guardar uma consulta não
compartilhada. O navegador pode conservar seus próprios históricos e caches;
o projeto não afirma controlar essa política. O link explícito não é secreto.

Modificar critérios depois de abrir um link compartilhado destaca a nova consulta
do fragmento antigo. A pessoa precisa compartilhar novamente para registrar a
versão nova. Isso evita que o endereço visível prometa filtros diferentes da tela.
A área de partidos é recolhível no mobile; seus botões não são recriados a cada
clique, preservando o foco. Há limpeza de partidos e da consulta completa.

Os verificadores anteriores de SP foram adaptados somente onde esperavam query
na URL a cada interação: agora abrem o compartilhador explícito e recarregam o
link resultante, preservando as verificações de registros, fontes e fotografias.
Os testes de IDs usam uma função de referência independente sobre os atributos e
associações originais, não a função de correspondência que está sob teste.

Referências de implementação: MDN, Window popstate event,
https://developer.mozilla.org/en-US/docs/Web/API/Window/popstate_event ;
MDN, URI fragment, https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Fragment .
'''
    if extra not in s:p.write_text(s+extra)

if __name__=='__main__':main()

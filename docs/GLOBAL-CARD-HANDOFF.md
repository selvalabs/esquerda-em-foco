# Handoff D2/D3 → #56

## Como reproduzir

No checkout do PR, com Python e as dependências do workflow:

```bash
python -m unittest discover -s tests/canonical_cards -p 'test_*.py' -v
python tools/canonical_cards/build.py --out /tmp/eef-card-prototype
python tests/canonical_cards/verify.py --prototype /tmp/eef-card-prototype --out /tmp/eef-card-evidence/preservation.json
python tests/canonical_cards/browser.py --prototype /tmp/eef-card-prototype --out /tmp/eef-card-evidence/browser
python -m http.server 8000 --bind 127.0.0.1 --directory /tmp/eef-card-prototype
```

Abrir `http://127.0.0.1:8000/prototipo.html`. A galeria apresenta 18 casos para revisão
de conteúdo rico, contexto parcial, histórico/mandato e lacunas. Não é ranking.
As seis páginas completas conservam busca, consulta, Selecionados e links.

## Saídas

- `audit/inventory.json`: estrutura e disponibilidade por edição;
- `audit/editorial-reconciliation.json`: precedência/decisões das versões por ficha;
- `audit/models.json`: observações e evidências com referência resolvível;
- `audit/inputs.json`: hashes das entradas;
- `audit/build.json`: resultado e hashes do build;
- capturas e relatório do navegador no diretório de evidências.

Nenhum HTML experimental é adicionado ao repositório ou ao sitemap. O build recusa
saída dentro do checkout. Não altera `config/editions.json` nem ativa novas
capabilities: isso pertence à #56, não a uma etapa implícita desta tarefa.

## Integração na #56

Renovar baseline, reconciliar qualquer atualização editorial posterior e verificar
as 20 entradas do contrato. Não restaurar arquivos antigos para satisfazer um
hash. Rever o inventário quando uma fonte mudar.

Aplicar `enhance_card` após o renderer editorial e antes dos hashes finais. Manter
os módulos de coleção/consulta e a exclusão dos rótulos de UI do índice de busca.
Não copiar as páginas do protótipo para produção: integrar a fonte do renderer
à cadeia `tools/global03/refresh.py`, testando duas gerações idênticas e todos os
caminhos de reconstrução autorizados. A #56 também ativa a gramática de filtros
da #53 e a compatibilidade do transporte; este protótipo não a antecipa.

Preservar os identificadores e as âncoras de todas as fontes; nenhum texto antigo
substituído por revisão deve ser reinserido sem revisão individual. Runtimes não
podem sobrescrever o padrão após um novo build editorial. Depois, conferir
publicação HTTP/SHA, mobile/desktop e leitura em Selecionados. RS Estadual continua
sujeita ao PR #9/issue #5; #50 estacionada; #57 e #44 mantêm gates próprios.

## Limites de verificação

O navegador testa Chromium em ambiente automatizado. Não equivale a teste em
aparelho físico, leitor de tela, certificação WCAG, envio WhatsApp ou reconferência
externa das fontes. Links de compartilhamento do protótipo apontam ao ambiente de
ensaio, não são apresentados como uma nova funcionalidade publicada.

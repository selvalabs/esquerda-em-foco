# RS-FED-03 — atualização manual e reprodução

## Estado e limites

O escopo original tinha 107 registros e 63 alvos editoriais. A correção canônica de partidos incorporada no `main` acrescentou quatro registros de PSTU/REDE, levando a base a 111. Os quatro registros foram preservados e receberam triagem separada; não são contados como integrantes do lote original de pesquisa.

O manifesto original permanece em `data/rs/rs-fed-03-targets.json`. A reconciliação concorrente está em `data/rs/fed03/integration-base.json`; os indicadores correntes e os motivos de lacuna estão em `docs/rs/fed03/`.

A pesquisa de pautas/atuação não certifica que todos os campos de uma ficha estejam completos. Os dados não são atualizados continuamente. Datas de consulta, datas de publicação e períodos históricos são distintos.

## Reprodução da versão consolidada

Utilizar uma cópia completa do repositório no commit de publicação, preservando seu histórico Git. O gerador reaproveita um template visual congelado por commit. O ZIP de entrega contém a página já gerada e seus recursos; ele não substitui o checkout completo necessário para reconstruir o projeto.

Dependências usadas na validação: Python 3.12; beautifulsoup4 4.13.4; lxml 6.0.2; Pillow 11.3.0; playwright 1.55.0, com Chromium instalado pelo Playwright.

```sh
python -m pip install beautifulsoup4==4.13.4 lxml==6.0.2 Pillow==11.3.0 playwright==1.55.0
python -m playwright install chromium
EEFOCO_OFFLINE_BUILD=1 PYTHONDONTWRITEBYTECODE=1 python tools/rs/build.py
python -m unittest discover -s tests/rs -p 'test_*.py' -v
python -m unittest discover -s tests/scope -p 'test_*.py' -v
python tools/rs/qa.py
python tools/rs/fed03_qa.py
```

No PowerShell, definir as variáveis antes do build:

```powershell
$env:EEFOCO_OFFLINE_BUILD = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
python tools/rs/build.py
```

`fed03_concurrent.py` e `fed03_install.py` são migrações idempotentes desta rodada, já aplicadas na versão consolidada. Não executar a migração antiga `upgrade_review.py` isoladamente sobre a versão RS-FED-03: ela foi criada para instalar a rodada anterior.

## Próxima revisão documental

1. Criar nova branch a partir do `main` mais recente e registrar commit, hash do HTML de SC e universo oficial. Não restaurar snapshots antigos sobre alterações concorrentes.
2. Preservar os relatórios desta rodada. Criar novo manifesto com as lacunas reais da base atual: não reutilizar automaticamente a lista de 63.
3. Pesquisar por ID eleitoral e identidade confirmada. Registrar consultas, fontes aceitas, fontes inacessíveis, localizadores, datas e motivos de rejeição. A mera menção a uma pauta ou uma página cadastral não autoriza atribuição individual.
4. Fazer coleta eleitoral explícita e compará-la com a versão anterior antes de substituir dados. A reconciliação por CSV não é equivalente a abrir cada perfil do DivulgaCand; erros 403 devem permanecer como falhas de acesso.
5. Nos históricos, manter `verified_nominal`, `not_applicable`, `not_verified`, `not_published_inapt` e `not_yet_held` separados. Os cinco registros históricos inaptos não ganharam votação zero; os dois conflitos de identidade originais continuam pendentes. Os três históricos trazidos pelos novos registros ainda requerem investigação.
6. Recalcular as contagens e executar testes/QA. Não atualizar números esperados nos testes sem evidência de mudança no universo ou no conteúdo correspondente.
7. Abrir PR, verificar o diff contra o `main` imediatamente anterior ao merge, publicar e comparar os hashes dos arquivos servidos com o commit integrado.

## Fronteiras de edição

As alterações desta rodada se limitam a `data/rs/`, `docs/rs/`, `tools/rs/`, `tests/rs/`, `rs/deputados-federais/` e workflows exclusivos `rs-fed03-*`. A configuração canônica compartilhada foi herdada do main e não modificada por este round. Não há novos filtros visuais, mudanças de ordenação ou atualização recorrente instalada.

## Empacotamento

Incluir a rota `rs/deputados-federais/`, os dados e as auditorias pertinentes. Não incluir o HTML raiz de SC como arquivo para substituição, caches Python, fontes tipográficas ou cópias integrais dos artigos coletados para leitura. O histórico da entrega e os números atuais devem permanecer separados.

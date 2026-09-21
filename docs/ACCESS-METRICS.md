# Métricas de acesso

## Decisões adotadas

- 1 acesso contabilizado por navegador a cada 24 horas.
- A navbar mostra somente o total geral do site.
- A contagem começa em zero quando o backend for ativado em produção.
- O backend mantém totais gerais, diários e por página.
- Endereços IP não são persistidos.
- O identificador aleatório do navegador é transformado em HMAC-SHA256 antes de ser armazenado.
- Persistência em PostgreSQL.
- Fuso de referência dos totais diários: `America/Sao_Paulo`.

## Estado no GitHub Pages

O frontend já está integrado, mas permanece desligado em:

`assets/metrics-config.js`

Enquanto `enabled: false`, nenhuma requisição de métricas é feita e nada aparece na navbar.

## Ativação na VPS

1. Subir PostgreSQL e criar um banco para o serviço.
2. Entrar em `server/metrics`.
3. Copiar `.env.example` para `.env` e preencher:
   - `DATABASE_URL`
   - `METRICS_HMAC_SECRET` com segredo aleatório longo
   - `ALLOWED_ORIGIN` com a URL pública final
4. Executar `npm install`.
5. Executar `npm run migrate`.
6. Subir o serviço em `127.0.0.1:8787` ou via container.
7. No proxy reverso, encaminhar `POST /api/metrics/visit` para o serviço.
8. Encaminhar `GET /healthz` apenas para monitoramento interno, se desejado.
9. Alterar `assets/metrics-config.js` para `enabled: true`.
10. Publicar o site na VPS.

## Contrato do endpoint

### Requisição

`POST /api/metrics/visit`

```json
{
  "siteId": "esquerda-em-foco",
  "pageId": "deputados-federais-sc",
  "visitorId": "UUID-v4-gerado-no-navegador"
}
```

### Resposta

```json
{
  "totalSite": 12437,
  "todaySite": 391,
  "totalPage": 9472,
  "todayPage": 288,
  "countedSite": true,
  "countedPage": true,
  "dedupeHours": 24
}
```

A navbar usa apenas `totalSite`.

## Privacidade

O navegador guarda um UUID aleatório em `localStorage`. O servidor nunca grava o UUID bruto:
ele produz um HMAC-SHA256 com `METRICS_HMAC_SECRET` e armazena somente o resultado.
Nenhum endereço IP é gravado nas tabelas de métricas.

O serviço ignora user-agents de bots conhecidos. A métrica é um contador operacional e não deve
ser tratada como auditoria absoluta de audiência: um usuário pode usar vários navegadores,
limpar o armazenamento local ou bloquear JavaScript.

## Falhas

O contador é não crítico. Timeout, indisponibilidade do banco ou erro do endpoint fazem o
contador simplesmente permanecer oculto. Busca, navegação e conteúdo continuam funcionando.

import http from 'node:http';
import crypto from 'node:crypto';
import {Pool} from 'pg';

const port = Number(process.env.PORT || 8787);
const connectionString = process.env.DATABASE_URL;
const secret = process.env.METRICS_HMAC_SECRET;
const allowedOrigin = process.env.ALLOWED_ORIGIN || '';

if (!connectionString) throw new Error('DATABASE_URL is required');
if (!secret || secret.length < 32) throw new Error('METRICS_HMAC_SECRET must be at least 32 characters');

const pool = new Pool({connectionString});
const BOT_RE = /bot|crawler|spider|slurp|preview|facebookexternalhit|whatsapp|telegrambot|discordbot/i;
const ID_RE = /^[a-z0-9][a-z0-9._:-]{0,79}$/i;
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type':'application/json; charset=utf-8',
    'Content-Length':Buffer.byteLength(payload),
    'Cache-Control':'no-store'
  });
  res.end(payload);
}

function visitorHash(visitorId) {
  return crypto.createHmac('sha256', secret).update(visitorId).digest('hex');
}

async function readJson(req) {
  let raw = '';
  for await (const chunk of req) {
    raw += chunk;
    if (raw.length > 16384) throw new Error('body-too-large');
  }
  return JSON.parse(raw || '{}');
}

async function countScope(client, {siteId, scope, hash}) {
  const guard = await client.query(
    `INSERT INTO metrics_visit_guard (site_id, scope, visitor_hash, last_counted_at)
     VALUES ($1,$2,$3,now())
     ON CONFLICT (site_id, scope, visitor_hash)
     DO UPDATE SET last_counted_at = EXCLUDED.last_counted_at
     WHERE metrics_visit_guard.last_counted_at <= now() - interval '24 hours'
     RETURNING 1`,
    [siteId, scope, hash]
  );

  const counted = guard.rowCount === 1;

  if (counted) {
    await client.query(
      `INSERT INTO metrics_daily (site_id, scope, visit_day, visits)
       VALUES ($1,$2,(CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date,1)
       ON CONFLICT (site_id, scope, visit_day)
       DO UPDATE SET visits = metrics_daily.visits + 1`,
      [siteId, scope]
    );
  }

  const totals = await client.query(
    `SELECT
       COALESCE(SUM(visits),0)::text AS total,
       COALESCE(SUM(visits) FILTER (
         WHERE visit_day = (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date
       ),0)::text AS today
     FROM metrics_daily
     WHERE site_id=$1 AND scope=$2`,
    [siteId, scope]
  );

  return {
    counted,
    total:Number(totals.rows[0].total),
    today:Number(totals.rows[0].today)
  };
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');

    if (req.method === 'GET' && url.pathname === '/healthz') {
      return json(res, 200, {ok:true});
    }

    if (req.method !== 'POST' || url.pathname !== '/api/metrics/visit') {
      return json(res, 404, {error:'not-found'});
    }

    if (allowedOrigin) {
      const origin = req.headers.origin || '';
      if (origin && origin !== allowedOrigin) return json(res, 403, {error:'origin-not-allowed'});
    }

    const userAgent = req.headers['user-agent'] || '';
    if (!userAgent || BOT_RE.test(userAgent)) {
      return json(res, 200, {ignored:true, totalSite:null});
    }

    const body = await readJson(req);
    const {siteId, pageId, visitorId} = body;

    if (!ID_RE.test(siteId || '') || !ID_RE.test(pageId || '') || !UUID_RE.test(visitorId || '')) {
      return json(res, 400, {error:'invalid-payload'});
    }

    const hash = visitorHash(visitorId);
    const pageScope = `page:${pageId}`;
    const client = await pool.connect();

    try {
      await client.query('BEGIN');
      const site = await countScope(client, {siteId, scope:'__site__', hash});
      const page = await countScope(client, {siteId, scope:pageScope, hash});
      await client.query('COMMIT');

      return json(res, 200, {
        totalSite:site.total,
        todaySite:site.today,
        totalPage:page.total,
        todayPage:page.today,
        countedSite:site.counted,
        countedPage:page.counted,
        dedupeHours:24
      });
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  } catch (error) {
    console.error(error);
    return json(res, 500, {error:'internal-error'});
  }
});

server.listen(port, '0.0.0.0', () => {
  console.log(`metrics service listening on :${port}`);
});

async function shutdown() {
  server.close(async () => {
    await pool.end();
    process.exit(0);
  });
}

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

CREATE TABLE IF NOT EXISTS metrics_visit_guard (
  site_id text NOT NULL,
  scope text NOT NULL,
  visitor_hash char(64) NOT NULL,
  last_counted_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (site_id, scope, visitor_hash)
);

CREATE TABLE IF NOT EXISTS metrics_daily (
  site_id text NOT NULL,
  scope text NOT NULL,
  visit_day date NOT NULL,
  visits bigint NOT NULL DEFAULT 0 CHECK (visits >= 0),
  PRIMARY KEY (site_id, scope, visit_day)
);

CREATE INDEX IF NOT EXISTS metrics_daily_site_day_idx
  ON metrics_daily (site_id, visit_day DESC);

CREATE INDEX IF NOT EXISTS metrics_guard_last_counted_idx
  ON metrics_visit_guard (last_counted_at);

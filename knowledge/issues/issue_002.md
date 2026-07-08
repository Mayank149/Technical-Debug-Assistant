# Issue 002: Postgres pool timeout under load

## Summary
API latency spikes and requests fail with connection pool timeout during traffic bursts.

## Environment
- PostgreSQL 15
- SQLAlchemy with pool size 20
- Gunicorn with 8 workers

## Reproduction
1. Run load test at 250 RPS for 5 minutes.
2. Monitor API error rate and DB connections.

## Observed behavior
- Timeouts begin after 2-3 minutes.
- `pg_stat_activity` shows long-lived idle transactions.

## Root cause
Sessions were not closed on exception paths, exhausting pool.

## Fix
Use request-scoped session management with `try/except/finally` and explicit `session.close()`.

## Follow-up
- Add dashboard for active and idle transactions.
- Alert when pool wait time exceeds threshold.

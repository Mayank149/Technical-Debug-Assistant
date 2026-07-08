# PostgreSQL Debug Notes

## Connection string template
`postgresql://user:password@host:5432/dbname`

## Common issue: too many connections
Symptoms: App intermittently fails with connection refused or pool timeout.
Actions:
- Reduce pool size at app level.
- Enable connection pooling (e.g., PgBouncer).
- Ensure sessions are closed after each request.

## Useful checks
```sql
SELECT datname, numbackends FROM pg_stat_database ORDER BY numbackends DESC;
SELECT pid, usename, state, query FROM pg_stat_activity LIMIT 20;
```

## Slow query troubleshooting
- Start with `EXPLAIN ANALYZE`.
- Add indexes for high-cardinality filter columns.
- Avoid `SELECT *` on large tables.

## Migration safety
- Backup before schema changes.
- Run migrations in staging with production-like data.
- Keep migrations idempotent where possible.

# Issue 001: Flask API returns 500 on /health

## Summary
After deployment, `GET /health` returns 500 instead of 200.

## Environment
- Python 3.11
- Flask 3.0
- Docker container on Linux host

## Reproduction
1. Build image using production Dockerfile.
2. Start container with default command.
3. Call `/health` endpoint.

## Observed behavior
Response:
```json
{"error": "Working outside of application context"}
```

## Root cause
Health blueprint tried to access `current_app.config` at import time.

## Fix
Move config access into request handler or initialization function that runs under app context.

## Regression test
Add integration test asserting `/health` returns HTTP 200 and JSON `{ "status": "ok" }`.

# Flask Debug Notes

## Common startup command
```bash
flask --app app run --debug
```

## Frequent errors

### Error: RuntimeError: Working outside of application context
Cause: A Flask extension or `current_app` is accessed before app context is pushed.
Fix: Wrap usage in `with app.app_context():` when running background scripts.

### Error: ImportError due to circular imports
Cause: `app.py` imports `routes.py` and `routes.py` imports `app`.
Fix: Use application factory pattern (`create_app`) and register blueprints.

## Production tips
- Use `gunicorn` or `waitress` instead of Flask development server.
- Set `FLASK_ENV` and `FLASK_DEBUG` only for local development.
- Return structured error JSON for API clients.

## Example health endpoint
```python
from flask import Blueprint, jsonify

health = Blueprint("health", __name__)

@health.get("/health")
def healthcheck():
    return jsonify({"status": "ok"}), 200
```

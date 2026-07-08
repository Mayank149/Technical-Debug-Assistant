# Docker Debug Notes

## Build and run
```bash
docker build -t tech-debug-assistant .
docker run -p 5000:5000 tech-debug-assistant
```

## Common issue: container exits immediately
Checks:
- Verify `CMD` or `ENTRYPOINT` is correct.
- Confirm app binds to `0.0.0.0` instead of `127.0.0.1`.
- Inspect logs: `docker logs <container_id>`.

## Common issue: image build is slow
- Reorder Dockerfile layers to maximize cache hits.
- Copy dependency files first, then install, then copy source.
- Use `.dockerignore` to exclude large folders.

## Networking notes
- Use service names in Docker Compose for inter-container DNS.
- Expose only required ports.

# Deploy — local compose and environments

Phase 2 §5.1 scaffolding only. There is no production platform here yet; this
folder makes the full loop runnable on one machine and documents how the same
images are configured for staging.

## Layout

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Base stack: PostgreSQL 16 + PostGIS, FastAPI API, Next.js web. |
| `docker-compose.dev.yml` | Hot-reload overrides (bind mounts, `--reload`, Next dev server). |
| `.env.example` | Local-only values; copy to `.env` (untracked). |
| `.env.staging.example` | Staging variable names; values come from the secret store. |
| `../backend/Dockerfile` | API image (runtime deps only, non-root, `/health` probe). |
| `../frontend/Dockerfile` | Web image (`deps` → `dev` → `build` → `runner`). |

## Local development

```bash
cp deploy/.env.example deploy/.env    # edit POSTGRES_PASSWORD if you like
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml up --build
```

| URL | Service |
| --- | --- |
| http://localhost:8000/health | API liveness |
| http://localhost:8000/docs | OpenAPI UI (dev only; disabled when `APP_ENVIRONMENT=production`) |
| http://localhost:3000 | Web client |

The API container runs `alembic upgrade head` before `uvicorn`. Migrations are
forward-only; the baseline revision `0001_baseline` is intentionally empty.

## Production-shaped run (no hot reload)

```bash
cp deploy/.env.example deploy/.env
docker compose -f deploy/docker-compose.yml up --build
```

## Staging and production

- Images are the same; only environment variables differ. `APP_ENVIRONMENT`
  is `dev`, `staging` or `production`; `production` hides `/docs` and
  `/openapi.json` unless `APP_DOCS_ENABLED=true` is explicitly set.
- **Secrets**: `POSTGRES_PASSWORD` (and any future API keys) come from the
  platform secret store or CI secret variables. Never commit a real value and
  never pass one on a command line that lands in shell history. Local values
  live only in untracked `deploy/.env`.
- TLS terminates at the platform ingress; compose does not publish 443.
- The base file requires `POSTGRES_PASSWORD` (`:?` guard) and fails closed
  when it is missing.

## Verification

```bash
# Parse and interpolate the stack without starting containers.
docker compose \
  --env-file deploy/.env.example \
  -f deploy/docker-compose.yml \
  -f deploy/docker-compose.dev.yml \
  config --quiet
```

CI runs the same command so a broken compose file fails the build.

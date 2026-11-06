# Backend — FastAPI modular monolith

**Status:** scaffold only. Implements no product feature yet.
**Stack:** Python 3.12+, FastAPI, Pydantic v2 (see `../docs-context/architecture-context.md`).

This is the runnable skeleton described in `../docs-context/phase-plan.md` §5.1. It
currently exposes health endpoints and the module layout; no domain logic exists.

## Layout

```
backend/
├── app/
│   ├── main.py            # application factory + root health route
│   ├── api/v1/            # routers: parse, authorise, delegate, serialise
│   ├── core/              # config, security, logging, errors
│   ├── modules/           # identity, observations, media, inference, ...
│   ├── db/                # session, base, models, repositories
│   └── workers/           # scheduled jobs
├── tests/
├── pyproject.toml
└── requirements.txt
```

## Commands (verified on this machine)

Run from `backend/`:

| Task | Command |
|---|---|
| Create venv | `python -m venv .venv` |
| Install | `.venv\Scripts\python -m pip install -r requirements.txt` |
| Tests | `.venv\Scripts\python -m pytest` |
| Dev server | `.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000` |

`GET /health` and `GET /v1/health` return the service status. OpenAPI is at `/docs`.

## Rules

- Routers parse, authorise, delegate and serialise. No business logic, no SQL.
- Repositories hold queries; services hold decisions.
- A module never imports another module's repository or ORM model.
- No endpoint returns model scores as a diagnosis; no chemical advice.
- Configuration comes from environment variables (`APP_` prefix) or `.env`; never secrets
  in code.

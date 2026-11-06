# PS-03 web client (Next.js + TypeScript)

API-only client for the PS-03 modular monolith. It consumes the versioned
`/v1` API and never connects to the database
(`final/docs-context/architecture-context.md`, ADR-003).

> Folder note: the source documents call this app `web/`; the implementation
> lives in `frontend/` because that folder already existed in the repository.
> See ADR-007 in `final/docs-context/progress-tracker.md`.

## Commands

```bash
npm install
npm run dev        # http://localhost:3000
npm run typecheck  # tsc --noEmit
npm run lint       # eslint .
npm run build      # production build
npm run start      # serve the production build
```

Set `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`) for browser
requests; see `.env.example`. Server components read `API_BASE_URL` first
(compose sets it to `http://api:8000`) so they use the container network while
the browser uses the public origin.

## Scope in Phase 2 §5.1

Engineering foundation only:

- `/` reports platform reachability and explains the two separate outputs.
- `/chat` is a chat shell that exercises the `/v1/conversations` contract,
  including idempotent retry via the same `client_message_id`.
- Demo responses from the API are labelled `demo` in the UI; the client never
  invents an assessment.

## Verified locally

| Command | Result |
| --- | --- |
| `npm run typecheck` | pass |
| `npm run lint` | pass |
| `npm run build` | pass (Next.js 16.4.5, Node 24) |

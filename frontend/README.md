# PS-03 web client (Next.js + TypeScript)

API-only client for the PS-03 modular monolith. It consumes the versioned
`/v1` API and never connects to the database
(`final/docs-context/architecture-context.md`, ADR-003).

> Folder note: the source documents call this app `web/`; the implementation
> lives in `frontend/` because that folder already existed in the repository.
> See ADR-009 in `final/docs-context/progress-tracker.md`.

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

## Routes

| Route | What it does | Evidence |
| --- | --- | --- |
| `/` | Reports API reachability and explains the two separate outputs. | live smoke, build |
| `/chat` | Conversation list: create, open and delete; empty and API-unreachable states. | live smoke, build |
| `/chat/[conversationId]` | Thread with structured assessment replies, idempotent retry, demo badge and delete. | live smoke, build |
| `/outlook` | Independent map-layer states (verified, unverified, modelled risk, coverage, boundaries) fetched from `/v1/map/layers/*`; explicit “not configured” state, never a merged risk value. | live smoke, build |
| `/review` | Honest “locked” state for the expert review portal; no fabricated cases. | live smoke, build |

The desktop shell is a persistent left sidebar (Overview, Photo assessment, Area
outlook, Review queue) with an active-section marker, a skip link and a top bar.
Below 1024px the sidebar collapses into a horizontal scrollable nav. Layout
reflows to a single column and the dashboard grids stack at 640px.

The web chat is the Phase 2 §5.7 surface, not a new model. It renders the
server's structured `AssessmentCard` fields; it never parses prose into a
diagnosis and never invents a result. An image attachment sends **filename
metadata only** — the upload/media pipeline and any real image model are not
connected in this phase.

## Design system

`design/tokens.json` is the semantic token source
(`final/feature-specs/01-design-system.md`). `app/globals.css` mirrors those
values as CSS variables until a generator exists; update both in one change.
Risk and status namespaces stay separate.

## Scope

Implemented:

- conversation list, thread, create and delete;
- honest placeholder routes for area outlook and expert review (no fabricated data);
- text and image-metadata composer (file picker and drag-and-drop, preview,
  10 MB guard);
- structured assessment card with assessed / abstained / unsupported / failed
  states, confidence band, calibration status, model version and generation
  time;
- demo labelling, offline notice, failed-send retry with the same
  `client_message_id`, and empty/error states.

Not implemented in this phase:

- image upload, presigned URLs and media storage;
- real image inference (replies are labelled demo);
- chat context fields (crop, stage, area) — the crop list is blocked on D1;
- expert review from chat, advisories, area outlook;
- authentication and per-user ownership (the backend uses a single demo owner);
- localisation catalogs (copy is currently English-only in components).

## Verified locally

| Check | Result |
| --- | --- |
| `npm run typecheck` | pass (2026-11-06) |
| `npm run lint` | pass (2026-11-06) |
| `npm run build` | pass; routes `/`, `/_not-found`, `/chat`, `/chat/[conversationId]`, `/outlook`, `/review` |
| Live smoke | `/`, `/chat`, `/outlook`, `/review` returned 200; `/chat/conv_missing` returned 404; the sidebar nav and platform status rendered. `/chat` listed a created conversation; the thread rendered title, demo badge and the abstained assessment; delete returned the empty state. `/outlook` rendered all five layer cards as “Not configured” with the new map router and “0 of 5 layers serving data”; no value was merged into a risk number |

The production build and live smoke used the local FastAPI dev server with the
in-memory demo conversation store. No real image upload or model inference was
exercised.

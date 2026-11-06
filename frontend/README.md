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
| `/chat` | Authenticated conversation list (staff sign-in required): create, open and delete; empty and API-unreachable states. Rows belong to the signed-in user only. | live smoke, build |
| `/chat/[conversationId]` | Authenticated thread with image upload, structured assessment replies, review requests, idempotent retry, demo badge and delete. Stored previews load with the bearer token (blob fetch). | live smoke (upload → assessment → review), build |
| `/outlook` | Authenticated independent map-layer states (verified, unverified, modelled risk, coverage, boundaries) fetched from `/v1/map/layers/*`; explicit “not configured” state, never a merged risk value. | live smoke, build |
| `/review` | Honest “locked” state for the expert review portal; no fabricated cases. | live smoke, build |
| `/admin` | Admin dashboard for the identity slice: staff sign-in + MFA, profile, account list/counts, provision staff, audited record view, role/status changes, retention and aggregate exports. Tokens stay in the tab's `sessionStorage`; unauthenticated, non-admin and expired states are explicit. | live smoke, build |

The desktop shell is a persistent left sidebar (Overview, Photo assessment, Area
outlook, Review queue, Admin) with an active-section marker, a skip link and a top bar.
Below 1024px the sidebar collapses into a horizontal scrollable nav. Layout
reflows to a single column and the dashboard grids stack at 640px.

The web chat is the Phase 2 §5.7 surface, not a new model. It renders the
server's structured `AssessmentCard` fields; it never parses prose into a
diagnosis and never invents a result. The composer uploads the photo to
`POST /v1/uploads` first and the message references the returned `upload_id`.
The server validates and stores the image, runs a demo quality gate and returns
a labelled demo assessment. No real image model is connected; the demo engine
(`demo-chat-0.1`) and all synthetic labels are visibly marked.

## Design system

`design/tokens.json` is the semantic token source
(`final/feature-specs/01-design-system.md`). `app/globals.css` mirrors those
values as CSS variables until a generator exists; update both in one change.
Risk and status namespaces stay separate.

## Scope

Implemented:

- staff sign-in (login + TOTP MFA) shared by chat, outlook and admin; tokens
  live in the tab's `sessionStorage` (see `lib/auth.ts`);
- authenticated conversation list/thread (create, open, delete), owner-scoped:
  each user sees only their own conversations, uploads and previews;
- honest placeholder route for expert review (no fabricated data);
- image composer with file picker, drag-and-drop, local preview and 10 MB guard;
- real upload to `/v1/uploads`, server-side validation and authenticated
  blob-preview rendering;
- structured assessment card with assessed / abstained / unsupported / failed
  states, quality flags, confidence band, calibration status, model version and
  generation time;
- request expert review from an assessment and see its persisted status;
- demo labelling, offline notice, failed-send retry with the same
  `client_message_id`, and empty/error states;
- authenticated independent map layers on `/outlook` (never merged);
- admin account list and role/status counts derived from the server list;
- staff provisioning (one-time MFA secret), audited record view with a
  required reason, role and status changes (staff-only, last-admin guards),
  credential retention and aggregate-only exports with required purposes.

Not implemented in this phase:

- presigned-URL/object-storage uploads (local multipart storage, owner-scoped
  token previews only);
- real image inference (replies are labelled demo);
- chat context fields (crop, stage, area) — the crop list is blocked on D1;
- the reviewer queue, advisories and area outlook;
- farmer phone-OTP sign-in (dev codes are held in backend memory and never
  returned over HTTP; no SMS provider — staff sign-in is the supported path);
- httpOnly-cookie sessions (tokens live in `sessionStorage`);
- localisation catalogs (copy is currently English-only in components).

## Verified locally

| Check | Result |
| --- | --- |
| `npm run typecheck` | pass |
| `npm run lint` | pass |
| `npm run build` | pass; routes `/`, `/_not-found`, `/admin`, `/chat`, `/chat/[conversationId]`, `/outlook`, `/review` |
| Live smoke | `/`, `/chat`, `/outlook`, `/review`, `/admin` returned 200; the sidebar nav (including Admin) and platform status rendered. Unauthenticated `/chat` and `/outlook` render the staff sign-in gate. Unauthenticated API calls return 401 without data; an authenticated user sees only their own conversations/uploads (verified live with two staff principals: list 0 vs 1, cross-read 404). Upload → message → review returned a persisted `demo-chat-0.1` assessment and review status under the owner's id; OpenAPI marks the chat/video/assessment/advisory/map routes `HTTPBearer`. `/outlook` (authenticated) rendered all five layer cards as “Not configured” with “0 of 5 layers serving data”; no value was merged into a risk number. `/admin` rendered the staff sign-in form while unauthenticated; the supporting API flows (login → MFA → profile/list, provision, audited view with reason, role/status guards, retention, aggregates, refresh rotation, 401/403 negative paths) were verified directly against the live backend |

The production build and live smoke used the local FastAPI dev server with a
file-backed SQLite database (the production schema is Alembic
`0002_chat_persistence`; PostgreSQL apply is not yet verified). The upload,
demo quality gate, demo assessment and review paths were exercised; no real
model inference was.

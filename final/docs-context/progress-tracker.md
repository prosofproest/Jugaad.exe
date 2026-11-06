# Progress tracker

**Single place to see where the project is, what is decided, and what comes next.**
Update this file in the same change as any scope, schema, API or decision change.

**Last updated:** 2026-11-06
**Current phase:** Phase 0 — Discovery (architecture decided in ADR-009/010/011; 5 of 12
blocking decisions answered; documentation reconciliation in progress; Phase 1 data platform
reference implementation verified in `database/` under recorded Gate-1 exception; no feature code)

---

## 1. Status legend

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done and verified |
| `[!]` | Blocked |
| `[-]` | Deferred / out of v1 |
| `[?]` | Decision required |

---

## 2. Phase plan and gates

Each phase must produce something a real user would use on its own. A phase does not
start until its gate is met. The detailed work, deliverables, owners and boundaries for
every phase are in `./phase-plan.md`; this section is the live status view.

### Phase 0 — Discovery `[~]`

- [x] Blueprint summarised and distilled into operating docs.
- [x] Full 55-chapter blueprint and Appendices A–H mapped to repository files (`../README.md`).
- [x] Realism audit applied; v1 scope narrowed.
- [x] Architecture baseline and feature specs drafted.
- [x] **Architecture** reconciled to PostgreSQL/PostGIS + Cloudinary + Next.js/React Native
      (`adr/0009-data-platform.md`, `adr/0010-v1-roles.md`, `adr/0011-open-crop-catalogue.md`).
- [x] **D1** Crop + targets policy decided: open catalogue + validated-target allowlist
      (ADR-011). The first concrete allowlist is split out as **D1a** (recorded in `phase-0/d1a-allowlist-decision.md`).
- [x] **D2** Nowcast (last 10 days) decided; 7-day outlook deferred.
- [~] **D3** Verifier role decided (extension-first, `can_confirm` permission; capacity
      and SLA documented in `phase-0/d3b-verifier-capacity-sla.md`; partner sign-off pending).
- [~] **D4** Owning/paying institution policy decided (`phase-0/d4-owning-institution.md`; partner counterparty pending).
- [x] **D5** Primary outcome metric pre-registered (`phase-0/d5-primary-metric.md`).
- [x] **D6** Advisory policy decided: non-chemical only (R5 unchanged).
- [~] **D7–D12** Scientific-integrity interim rules recorded in `phase-0-decisions.md` §7.
- [x] **D13** v1 languages decided: English + Kannada.
- [x] **D14** Output semantics decided: confidence band + abstention; severity is an
      expert-review field.
- [x] **D15** Notification channels decided: in-app mandatory; email for staff; SMS optional;
      WhatsApp/push/IVR deferred.
- [x] Crop calendar and epidemic window documented for the pilot area (`phase-0/crop-calendar.md`, `phase-0/target-reference-sheet.md`, `phase-0/pilot-sites.csv`).

**Gate 0:** D1–D12 answered and recorded in §4, each with a recorded date and one named
accountable owner. Gate 0 carries a calendar target (proposed: **2026-11-20**, confirmed at
the decision workshop) so that it cannot close by definition. No code that depends on them.
Working record: `phase-0-decisions.md` and `phase-0/`. **Gate 0 is decision-drafted; partner signatures pending.**

### Phase 1 — Data foundation `[~]`

- [~] Partner MoUs and data-permission records (registers created in `database/governance/`; signatures pending).
- [~] Image collection protocol and consent wording (drafted in `database/collection/` and `database/governance/03-consent-wording-and-capture.md`).
- [~] Labelling handbook (taxonomy, uncertainty classes, severity, provenance drafted in `database/labelling/`).
- [~] Plant-clinic archive access assessed (protocols drafted in `database/archive/`).
- [ ] Weather provider and boundary dataset chosen, licence recorded.
- [x] Database schema implemented and migrated (`05-data-layer.md` — 14 slices, 39 tables, append-only triggers, PostGIS spatial boundary, Alembic migrations, demo seed in `database/`; 14 tests verified).
- [~] Data dictionary v1; quality checks for each ingestion batch (v1 drafted in `database/data-dictionary/`).
- [x] Quarantine path for suspicious records (`database/governance/06-quarantine-policy.md`).

**Gate 1:** documented permissions for every dataset; reproducible ingestion; label
handbook approved by a `can_confirm` holder and an agronomist.

### Phase 2 — Platform MVP `[~]`

- [x] **§5.1 Engineering foundation** — backend/web/mobile scaffolds, CI,
      Alembic baseline, local compose, dev/staging env templates, structured
      logging, OpenAPI/error contract and `../TEST-MATRIX.md`.
- [~] Auth, roles, consent (`03-auth-and-roles.md`): Backend identity service, phone OTP,
      staff MFA, JWT tokens, RBAC, scoped permissions (`can_confirm`, `can_approve_advisory`),
      consent capture in `backend/app/api/v1/auth.py`.
- [ ] Mobile context + capture + quality feedback + offline queue (`02-...`): Flutter shell committed; capture UI pending.
- [~] Observation API with idempotency and signed uploads: `POST /v1/observations`,
      `POST /v1/observations/{id}/images`, `POST /v1/observations/{id}/images/{id}/confirm` in `backend/app/api/v1/observations.py`.
- [~] Web frontend shell + mobile app shell consuming the same `/v1` API (`frontend/` and `mobile/`).
- [~] Conversational capture: `conversations` module + chat on web and mobile
      (`08-conversational-capture.md`). **Web surface built** against the
      demo backend: conversation list/thread, structured assessment
      card, metadata-only image composer, idempotent retry and delete.
- [x] Chat reply contract (`assessment`, `abstained`, `unsupported_crop`, `queued`, `failed`,
      `review_requested`) and chemical-content validator (`backend/app/modules/assessments/explanation.py`, `backend/app/modules/advisories/validator.py`).
- [~] Expert review queue and decision flow (`04-expert-review.md`): Triage queue, claim,
      decision, notes in `backend/app/api/v1/review.py` and `modules/review/service.py`.
- [~] Audit trail for reviews, roles, exports and chat events (`backend/app/modules/audit/service.py`, `database/schema/01-schema.sql`).
- [~] Admin config for crops, targets, geographies (`backend/app/api/v1/forecast.py`, `backend/app/db/seed.py`).
- [ ] End-to-end test: report → upload → review, including airplane mode.
- [ ] End-to-end test: chat image → structured reply on web and mobile, retry idempotent.

**Gate 2:** a report can be captured offline, synced once, reviewed, and audited, on a
low-end device; chat image → assessment works on web and mobile. No predictive model
required; any demo reply is labelled.

### Phase 3 — Image AI `[ ]`

- [ ] Quality gate model (blur, exposure, resolution, no-plant).
- [ ] Field-image baseline; public data used for pretraining only.
- [ ] Group-held-out field test set frozen before model selection.
- [ ] Calibration + abstention thresholds chosen on validation.
- [ ] Evaluation report: macro F1, per-class recall, ECE, abstention rate, subgroups.
- [ ] ONNX export, registry entry, versioned serving.
- [ ] Result card with top-3, confidence band, quality flags, escalation.

**Gate 3:** the D8 floors are **met**, not merely reported, at the shipped abstention
threshold on the frozen field-only test set, with sample counts and confidence intervals;
abstention behaviour is reported on hard negatives. A performance number that does not
clear the pre-registered floor fails the gate.

### Phase 4 — Forecasting `[ ]`

- [ ] Event definition and spatial unit documented (`06-...`).
- [ ] Versioned, expert-approved rules baseline (e.g. blight risk index).
- [ ] Weather ingestion with source timestamps and freshness checks.
- [ ] Feature snapshot persisted per forecast run.
- [ ] No-score behaviour for stale/low-coverage inputs.
- [ ] Risk bands with operational meanings and approved actions.
- [ ] Separate map layers + coverage panel.
- [ ] Temporal holdout evaluation; calibration report.
- [ ] Alert trigger, dedupe, cooldown, delivery status.

**Gate 4:** the D7 event definition and label maturity rule are fixed and frozen before the
test season; the D9 coverage, freshness and suppression values are recorded and approved;
the forecast is reproducible from a stored snapshot; the no-score path is verified against
those values; the map never merges reports and predictions.

### Phase 5 — Pilot `[ ]`

- [ ] Site selection and control/matched design documented.
- [ ] Silent phase running (predictions not shown).
- [ ] Comparison with field observations; false alerts and missed events logged.
- [ ] Limited alert phase with approved templates and escalation owners.
- [ ] Usability and comprehension rounds with farmers and extension workers.
- [ ] Lead-time measurement against baseline.
- [ ] Weekly review cadence and issue log.

**Gate 5:** silent-phase evidence reviewed against the D5 pre-registered metric; alert
response workflow staffed; every logged safety issue either closed or explicitly accepted in
writing by the D6 owner ("unresolved" means neither, and blocks). Pilot timed to the
epidemic season.

### Phase 6 — Rollout `[ ]`

- [ ] Operational runbooks, on-call ownership, incident response.
- [ ] Backups and restore tested; RTO documented.
- [ ] Monitoring dashboards for data, model, product metrics.
- [ ] Training for extension staff and admins.
- [ ] Controlled expansion criteria written and approved.
- [ ] Launch-readiness checklist (blueprint Appendix H) signed off.

**Gate 6:** all launch gates met. If not, feature stays silent/non-operational.

---

## 3. Workstream status

| Workstream | Status | Next action |
|---|---|---|
| Documentation | `[~]` | Reconcile remaining specs to ADR-009/010/011 |
| Blueprint coverage | `[x]` | Chapter map maintained in `../README.md` |
| Architecture | `[x]` | ADR-009/010/011 accepted; propagate to specs |
| Decisions | `[~]` | Close D1a, D3b, D4, D5, D7–D12 |
| Data acquisition | `[ ]` | Identify archive partners; draft MoU |
| Labelling | `[ ]` | Draft handbook after D1a |
| Data platform | `[x]` | Reference schema (39 tables), migration, storage rules, backup design, and demo seeds verified in `database/`; `backend/` remains schema authority |
| Backend | `[~]` | FastAPI health scaffold, error handling, session/models, and v1 API router scaffolds |
| Mobile | `[~]` | Flutter shell committed; CI analyze/test job defined |
| Web | `[~]` | Next.js shell in `frontend/`; typecheck, lint and build pass |
| Chat | `[~]` | Spec 08 + in-memory demo chat API + web/mobile shells; real assessment waits on Phase 3 |
| Image ML | `[ ]` | Baseline on public data for pipeline only |
| Forecast | `[~]` | Rules baseline, domain models, features and forecast API scaffolded in `backend/` |
| MLOps | `[~]` | `model_registry` schema, triggers, checksum verification, and demo entries implemented in `database/` |
| Security/privacy | `[~]` | Object storage rules (TTL ≤ 10m) & RBAC matrix implemented; DPIA drafted |
| Pilot ops | `[ ]` | Site list and verification capacity after D3 |

---

## 4. Decisions (blocking)

Record: decision, options, consequence, owner, date. Do not delete history.

Every decision carries **one named accountable owner** and a **`Needs by` date tied to a
phase gate**. A decision with neither cannot be counted as answered, and Gate 0 cannot
close while any remain open. Where a decision needs a number that the repository is not
entitled to invent (R6), the decision must still define *who sets the number, from what
measurement, before which gate* — the rule for setting the value is itself the decision.

### D1 — Crop + targets + zone `[x]`

**Decision (2026-11-06):** Open, crop-agnostic catalogue with a **validated-target
allowlist** (ADR-011). Any crop may be submitted; an assessment is returned only for a
`crop × target` pair on the release allowlist; everything else returns an explicit
abstention (`unsupported_crop`, `unsupported_target`, `insufficient_quality`). The first
concrete allowlist is tracked as **D1a** and must be fixed before Gate 3.
**Owner:** Project owner + agronomist. **Decided:** 2026-11-06. **Needs by:** Gate 0 (met).

| Option | Consequence |
|---|---|
| Potato late blight | Validated weather model exists (BLITECAST/SimCast); forecast credible on day one; narrow advisory |
| Tomato late blight / early blight / leaf curl | More targets, more public data, weaker forecast baseline for non-blight targets |
| Rice blast / BLB / brown spot | Large farmer base, harder image data, blast weather models exist |
| Open catalogue + allowlist (chosen) | Crop-agnostic schema; claims limited to validated entries; abstains elsewhere |

### D2 — Nowcast or 7-day outlook `[x]`

**Decision (2026-11-06):** **Nowcast over the last 10 days** for v1. A 7-day outlook is
deferred until at least one season of verified outcomes exists.
**Owner:** Agronomist + ML lead. **Decided:** 2026-11-06. **Needs by:** Gate 0 (met).

| Option | Consequence |
|---|---|
| Nowcast (last 10 days) (chosen) | No historical outcome data needed; more accurate; still actionable |
| 7-day outlook | Needs validation against outcomes; risk of overclaiming in year one |

### D3 — Verifier, capacity, SLA `[~]`

**Decision (2026-11-06):** Extension-first verification, with `confirmed` requiring the
scoped `can_confirm` permission; `admin` does not verify (ADR-010). **Still open:** review
SLA, capacity per area, escalation path and the minimum number of `can_confirm` holders.
**Owner:** Programme lead + partner. **Needs by:** Gate 0 for SLA/capacity.

| Option | Consequence |
|---|---|
| Extension-worker-first (chosen) | Scales; needs training and triage rules; senior reviewer confirms |
| Pathologist-first | Higher label quality; immediate backlog; not viable at volume |

### D4 — Owning/paying institution `[~]`

Policy decided (2026-11-06): Public extension/plant-health authority as institutional owner; grant/NGO-funded pilot transitioning to institutional or cooperative operations. Input-company funding for the advisory layer is rejected on trust grounds. See [`phase-0/d4-owning-institution.md`](phase-0/d4-owning-institution.md). Named counterparty (D4a) pending partner signature.
**Owner:** Product lead. **Needs by:** Gate 0.

### D5 — Primary outcome metric `[x]`

**Pre-registered (2026-11-06):** **Median lead time from first farmer report to verified expert
confirmation**, versus the existing advisory baseline. Secondary:
prioritisation accuracy, false-alert burden. Pre-registered in [`phase-0/d5-primary-metric.md`](phase-0/d5-primary-metric.md).
**Owner:** Product lead + evaluator. **Decided:** 2026-11-06. **Needs by:** Gate 0 (met).

### D6 — Legal position on advisory content `[x]`

**Decision (2026-11-06):** **Non-chemical only.** Advisory content is expert-approved,
versioned and limited to scouting, monitoring, sanitation, crop management and escalation.
No pesticide, herbicide, fungicide, dosage, mixture or pre-harvest-interval content. R5 is
unchanged. Legal review is still required before Gate 5.
**Owner:** Programme lead + legal. **Decided:** 2026-11-06. **Needs by:** Gate 0 (met).

| Option | Consequence |
|---|---|
| Non-chemical only (chosen) | Lowest liability; matches R5; no chemical content |
| Approved chemical content with legal sign-off | Would require weakening R5 and a formal liability review |
| No advisory in v1 | Weakens the product; alerts only |

### D7 — Forecast event, negative class and label eligibility `[?]`

The forecast track currently has no observable negative class, and `probable` may or may not
count as verified — two readings are both valid today.

| Option | Consequence |
|---|---|
| Presence / first-verified-case event | No denominator needed; cannot report PR-AUC or Brier honestly; must be framed as positive-unlabelled |
| Scheduled absence sampling (scouting rounds record verified negatives) | Enables real discrimination metrics; needs field capacity per D3 |

Must also decide: whether `probable` is eligible for forecast features (recommended: yes,
with an evidence tier, and `unverified` never eligible); the as-of label rule
(`verified_at <= cutoff`, event date <= cutoff); and the label-maturity embargo before a
season is frozen as test data.
**Owner:** ML lead + agronomist + pathologist. **Needs by:** Gate 0; frozen before Gate 4.
**Blocks:** `06-forecast-and-risk-map.md` §6, `04-expert-review.md` §16 Q2, `05-data-layer.md`
`observation_verification`.

### D8 — Abstention rule and numeric acceptance floors `[?]`

Decision function (e.g. calibrated max-probability below τ, plus margin/entropy and an
out-of-distribution distance), per-class τ, risk–coverage target, and the override policy
with audit fields — **plus the numeric floors** for Gates 3–5: minimum per-class recall,
maximum abstention rate, minimum share of area-days scored, and minimum lift over a
climatology/naive baseline.

R6 forbids inventing these numbers. The decision is therefore the *rule*: measure the
Phase-3 baseline, then pre-register the floors in this section before the frozen test set is
opened. Floors set after seeing test results are void.
**Owner:** ML lead + product lead + evaluator. **Needs by:** before Gate 3 exit.
**Blocks:** Gate 3, Gate 4, `ml-models.md` §abstention, `01-design-system.md` confidence bands.

### D9 — Coverage, freshness and suppression values `[?]`

Coverage formula with numerator, denominator and window (active reporters per area per
window, report completeness, weather freshness, representativeness — **not** reporter count
alone, which is gameable); the minimum value that permits a scored band and an alert; the
weather freshness threshold; the aggregation unit and coordinate precision; and the small-
count suppression threshold applied consistently to map, API and exports.
**Owner:** Data engineer + product lead + legal. **Needs by:** Gate 4.

### D10 — Retention, deletion and derived-data policy `[?]`

Per-entity deletion matrix including `image_predictions`, `feature_snapshots`, the frozen
test set, backups and trained weights; whether model weights are derived personal data;
tombstone erasure applied on restore; on-device TTL, encryption at rest and wipe-on-logout
for unsent images; and the named data controller (see also `03-auth-and-roles.md` §13 Q3).
**Owner:** Programme lead + legal + engineering lead. **Needs by:** Gate 2 (capture starts
there, so the policy must precede it).

### D11 — Identity model for on-behalf capture and offline sessions `[?]`

Separate `reporter_id` (actor) from `subject_user_id` (farmer) with on-behalf authorisation;
object-level access rules; idempotency scope; and the offline session policy — maximum
offline period, whether capture continues after the 15-minute access token expires, and how
role revocation and logout-all reach a device that is offline for ≥ 7 days (required by
`02-reporting-and-capture.md` §8).
**Owner:** Backend lead + product lead. **Needs by:** Gate 2.

### D12 — Client-side quality pre-check mechanism `[?]`

FR-02-07 requires an on-device pre-check, while `architecture-context.md` §2 rejects
on-device inference and `02-reporting-and-capture.md` §11 lists it as out of scope.
Decide: deterministic heuristics (blur/exposure/resolution) with plant-presence as
guidance only, or a small on-device model (which needs an ADR reversing the architecture
stance). Record framework, size, thresholds, latency and battery budget, and state what an
offline user sees between capture and sync.
**Owner:** Mobile lead + ML lead. **Needs by:** Gate 2.
**Interim rule until decided:** the client pre-check is advisory only. It must never block
saving or submitting a report (R8), and the server quality gate remains authoritative for
assessment (FR-02-12).

### D13 — v1 languages `[x]`

**Decision (2026-11-06):** **English + Kannada** in v1, with a language switcher and
persisted choice. All user-facing strings are externalized, including backend-generated
error and alert text.
**Owner:** Product lead. **Decided:** 2026-11-06. **Needs by:** Gate 2.

### D14 — Confidence and severity semantics `[x]`

**Decision (2026-11-06):** Display a **qualitative confidence band plus abstention** by
default. A numeric probability is shown only when calibration has been measured and passed
for that allowlist entry. **Severity is an expert-review field**, not a model claim. Photo
assessment and area outlook remain separate (R1).
**Owner:** ML lead + product lead. **Decided:** 2026-11-06. **Needs by:** Gate 3.

### D15 — Notification channels `[x]`

**Decision (2026-11-06):** **In-app is mandatory** on web and mobile. **Email** is used for
staff and institutional recipients. **SMS is optional** per pilot partner and sits behind
an adapter interface. **WhatsApp, push and IVR are deferred** beyond v1.
**Owner:** Product lead + programme lead. **Decided:** 2026-11-06. **Needs by:** Gate 5.

| Option | Consequence |
|---|---|
| In-app mandatory; email staff; SMS optional (chosen) | No dependency on a messaging provider to launch; adapter keeps SMS switchable |
| SMS/WhatsApp primary | Requires a Business API contract and template approval before launch |
| In-app only | Simplest, but excludes feature-phone farmers |

---

## 5. ADR log

| ID | Decision | Status | Date |
|---|---|---|---|
| ADR-001 | Modular monolith over microservices | Accepted | 2026-11-06 |
| ADR-002 | FastAPI + SQLAlchemy/Alembic as single schema authority (no Prisma) | Accepted | 2026-11-06 |
| ADR-003 | Web portals are API-only clients | Accepted | 2026-11-06 |
| ADR-004 | Rules-based forecast before ML | Accepted | 2026-11-06 |
| ADR-005 | ONNX Runtime CPU inference for pilot | Proposed | 2026-11-06 |
| ADR-006 | Flutter capture + SMS/WhatsApp delivery | Superseded by ADR-009/010 | 2026-11-06 |
| ADR-007 | Full-stack delivery: one API, web app and mobile app are all in scope | Accepted | 2026-11-06 |
| ADR-008 | Chat is a `conversations` wrapper over photo assessment, not a new model or generative diagnosis | Accepted | 2026-11-06 |
| ADR-009 | PostgreSQL/PostGIS + Cloudinary as the v1 data platform | Accepted | 2026-11-06 |
| ADR-010 | v1 roles: farmer, extension_worker, admin; `can_confirm` for confirmation | Accepted | 2026-11-06 |
| ADR-011 | Open crop catalogue with a validated-target allowlist | Accepted | 2026-11-06 |

---

## 6. Risk register

| ID | Risk | L | I | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-01 | No verified historical data in year one | H | H | Rules baseline; nowcast; state limits | ML lead | Open |
| R-02 | Public-data model fails in field | H | H | Field test set; domain adaptation; quality gate | ML lead | Open |
| R-03 | Verification backlog empties the verified layer | H | H | Extension-first triage; SLA; workload caps | Programme | Open |
| R-04 | "No reports" read as "no disease" | M | H | Coverage as feature + UI; suppression rules | Product | Open |
| R-05 | Advisory liability | L | H | Non-chemical only; approval workflow; legal review | Programme | Open |
| R-06 | Privacy breach (location/identity) | L | H | Approximate location; RBAC; audit; DPIA | Eng lead | Open |
| R-07 | Pilot misses epidemic season | M | H | Calendar-driven planning | Programme | Open |
| R-08 | Partner withdrawal mid-pilot | M | H | Dual partnerships; data ownership agreement | Product | Open |
| R-09 | False-alert fatigue | M | M | Calibration; cooldown; feedback loop | Product | Open |
| R-10 | Scope creep (multi-crop, universal diagnosis) | H | H | Expansion rule; Gate 0 decisions | Product | Open |
| R-11 | Look-alike symptoms mislabelled as disease | H | M | Abiotic class; label handbook; expert review | Agronomist | Open |
| R-12 | Low-coverage area read as low risk | H | H | Coverage gate blocks scored bands; UI coverage panel | Product | Open |
| R-13 | Biosecurity: public map used to infer farm vulnerability | L | H | Aggregation, suppression, access control | Eng lead | Open |
| R-14 | Adversarial input (borrowed/gamed images) | M | M | Provenance metadata; duplicate detection; spot checks | Field ops | Open |
| R-15 | Expert burnout from unpaid review labour | M | H | Workload caps; compensation; triage | Programme | Open |
| R-16 | Weather provider outage, gap or licence change | M | H | Freshness checks; `insufficient_data` path; provider terms recorded | Data engineer | Open |
| R-17 | Chat reply read as a diagnosis | H | H | Structured templates; "assistive, not diagnosis" copy; abstention; review escalation | Product | Open |
| R-18 | Chat emits chemical advice or free-form medical text | L | H | Server-side validator before storage; template tests; no generative diagnosis path in v1 | Eng lead | Open |
| R-19 | Chat scope creep into a general LLM assistant | M | M | Explicit out-of-scope; wrapper-only architecture; no free-form model | Product | Open |

L = likelihood, I = impact, both H/M/L.

---

## 7. Changelog

| Date | Change |
|---|---|
| 2026-11-06 | Created `docs-context/` and `feature-specs/` from `summary.md`, `totalcontent.md`, `update.md`. v1 scope narrowed per realism audit. Six decisions recorded as open. |
| 2026-11-06 | Aligned the full documentation set to the supplied 55-chapter blueprint. Added `data-foundation.md`, `ml-models.md`, `operations-and-pilot.md`, `roadmap-and-resources.md`, `appendices.md`, and the chapter map in `README.md`. Expanded overview, architecture, UI, code standards, workflow rules and feature specs. No scope decision changed; D1–D6 remain open. |
| 2026-11-06 | Added `phase-plan.md`: a detailed per-phase work breakdown (workstreams, deliverables, exit gates, owners, dependencies and explicit exclusions for Phases 0–6). Linked it from the README, `AGENTS.md`, `project-overview.md` and `roadmap-and-resources.md`. No gate, scope or decision changed. |
| 2026-11-06 | Added `final/PRD.md` and `final/TRD.md`: consolidated product and technical requirements distilled from the operating docs, feature specs and phase plan. No gate, scope or decision changed. |
| 2026-11-06 | Loophole audit applied. Added decisions D7–D12 (forecast event/negative class, abstention rule + numeric floors, coverage/freshness/suppression values, retention/deletion, on-behalf identity + offline sessions, client pre-check mechanism). Gate 0 now needs a calendar target and named owners; Gates 3–5 now require floors to be **met**, not merely reported, and require D7/D9 values. Fixed internal contradictions: `ui-context.md` status tokens and calibration copy, `01-design-system.md` status token list, `TRD.md` raw-score example, `02-reporting-and-capture.md` on-device scope, `code-standards.md` ADR gating, `AGENTS.md` scope wording. Findings: `../audit/loopholes-2026-11-06.md`. |
| 2026-11-06 | Made full-stack delivery explicit (backend API + Next.js web app + Flutter mobile app) and added `feature-specs/08-conversational-capture.md`: chat on web and mobile where a user sends an image and receives a structured, validator-checked assessment reply. Updated PRD, TRD, architecture, UI, phase plan, AGENTS and READMEs. Added ADR-007/008 and R-17–R-19. |
| 2026-11-06 | **Phase 0 architecture reconciliation.** Accepted ADR-009 (PostgreSQL/PostGIS + Cloudinary), ADR-010 (three roles: farmer, extension_worker, admin; `can_confirm` permission), ADR-011 (open crop catalogue + validated-target allowlist). Answered D1, D2, D6, D13 (English + Kannada) and D14 (confidence band + abstention; severity is an expert field). Added D15 (in-app/email/SMS channels). Added `phase-0-decisions.md`. Gate 0 remains open on D1a, D3b, D4, D5 and D7–D12. |
| 2026-11-06 | Added Phase 1 reference artifacts in `database/`: complete schema slices (39 tables) against `05-data-layer.md`, Alembic migrations, object storage / presigned rules, backup and recovery design, demo-seed policy (`is_demo = true`, R5 non-chemical compliance), and 14 schema/storage tests passing. |
| 2026-11-06 | Reconciled `../../IMPLEMENTATION-CHECKLIST.md` against the repository: updated work log for Phase 1 data platform, backend foundations, API router scaffolds, and test evidence. |

---

## 8. Next five actions

1. Fix **D1a** (first validated crop/target allowlist) and **D3b** (verifier capacity + SLA).
2. Record **D4** (owning institution) and **D5** (primary metric) with named owners.
3. Propagate ADR-009/010/011 into `architecture-context.md`, `feature-specs/03`, `feature-specs/05`, `PRD.md` and `TRD.md`.
4. Close D7–D12 or record explicit interim rules with owners and dates.
5. Draft data acquisition plan, partner MoUs, and labelling handbook after D1a.

---

## 9. Team and ownership

From blueprint Chapter 49. Roles are named here; individuals are assigned at Gate 0.

| Role | Owns | Accountable for |
|---|---|---|
| Product lead | Scope, research, milestones, stakeholder communication | Acceptance and decisions D1–D6 |
| Agronomist / pathologist | Taxonomy, labels, risk rules, advisory approval | Data and advisory correctness |
| Data engineer | Ingestion, quality, geospatial processing, lineage | Data foundation gates |
| ML engineer | Image and forecast modelling, evaluation, calibration, monitoring | Model gates and honesty |
| Application engineers | Mobile, backend, portal, APIs, offline sync | Platform MVP gate |
| QA and field researcher | Test strategy, usability, field pilot, issue reporting | Pilot evidence quality |
| Field operations lead | Partner coordination, verification capacity, training | Review SLA and coverage |

**Implementation points**

- One accountable owner per deliverable.
- Regular field feedback sessions throughout development.
- Staffing shape is 7–9 people for v1; the first operational hire after engineering is a
  field operations lead.

---

## 10. Budget and resources

From blueprint Chapter 51. No figure is committed until the work breakdown and the owning
institution (D4) are settled.

| Category | Cost driver |
|---|---|
| People | Engineering, data, ML, agronomy, field collection, QA, support |
| Data acquisition | Field visits, enumerators, expert labelling, lab confirmation, licences |
| Infrastructure | CPU inference, training GPU, database, storage, maps, monitoring, backups |
| Operations | Connectivity, devices, training, translation, support, maintenance |
| Risk reserve | Seasonal delay, provider change, extra collection |

Guidance: people and field data dominate; infrastructure is usually under 10% at pilot
scale. Prepare low, expected and high scenarios and track recurring cost separately from
one-time development. See `roadmap-and-resources.md` §2.

---

## 11. Success metrics (pre-registration)

From blueprint Chapter 53. Baselines and targets are set with domain experts **after** the
baseline is measured; no target numbers are committed here.

| Level | Metrics |
|---|---|
| Technical | Image macro F1, per-class recall, calibration, abstention rate; forecast PR-AUC, Brier, calibration; latency |
| Operational | Report-to-review time, backlog, verified case rate, delivery, sync success |
| User | Task completion, comprehension, repeat use, alert usefulness, opt-out |
| Agricultural | Lead time, visit prioritisation, credible outcome indicators |
| Equity | Performance and adoption by geography, device and segment |

**Primary metric (D5):** median lead time from first farmer report to verified expert
confirmation, versus the existing advisory baseline. Pre-register before the pilot.

---

## 12. Documentation coverage

The supplied blueprint (`../totalcontent.md`) is 55 chapters plus Appendices A–H. Coverage:

| Range | Document |
|---|---|
| Ch 1–10 | `project-overview.md` |
| Ch 11–12 | `../feature-specs/02`–`08`, `code-standards.md` |
| Ch 13–14, 43, 47, 48 | `architecture-context.md` |
| Ch 15–17 | `ui-context.md` |
| Ch 18–24 | `data-foundation.md` |
| Ch 25–26 | `../feature-specs/05-data-layer.md` |
| Ch 27–38 | `ml-models.md` |
| Ch 39 | `../feature-specs/06-forecast-and-risk-map.md` |
| Ch 40–44 | `../feature-specs/07-advisory-and-alerts.md`, `../feature-specs/02-reporting-and-capture.md`, `../feature-specs/03-auth-and-roles.md`, `ml-models.md` |
| Ch 45–49, 53–55 | `operations-and-pilot.md` |
| Ch 50–52 | `roadmap-and-resources.md` |
| Appendices A–H | `appendices.md` |

The chapter-to-file map is maintained in `../README.md`. Coverage is documentation, not
scope approval.

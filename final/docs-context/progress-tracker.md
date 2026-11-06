# Progress tracker

**Single place to see where the project is, what is decided, and what comes next.**
Update this file in the same change as any scope, schema, API or decision change.

**Last updated:** 2026-11-06
**Current phase:** Phase 0 — Discovery (documentation complete, decisions open; Phase 2 §5.1
engineering foundation, the persisted demo chat slice, the demo-labelled video-reading
machinery and the §5.2 identity backend slice present under a recorded Gate-1
exception; no live model key configured and no durable identity store; mobile
analyze/test verified locally)

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
- [ ] **D1** Crop + 3–5 targets + agro-climatic zone selected with local experts.
- [ ] **D2** Nowcast vs 7-day outlook decided.
- [ ] **D3** Verifier role, capacity and SLA agreed with partner.
- [ ] **D4** Owning/paying institution identified.
- [ ] **D5** Primary outcome metric pre-registered.
- [ ] **D6** Legal position on advisory content confirmed.
- [ ] **D7–D12** Scientific-integrity decisions recorded (see §4).
- [x] **D13** Agronomist role model recorded (see §4).
- [ ] Crop calendar and epidemic window documented for the pilot area.

**Gate 0:** D1–D13 answered and recorded in §4, each with a recorded date and one named
accountable owner (D7 and D13 are already accepted). Gate 0 carries a calendar target
(proposed: **2026-11-20**, confirmed at the decision workshop) so that it cannot close by
definition. No code that depends on them.

### Phase 1 — Data foundation `[ ]`

- [ ] Partner MoUs and data-permission records.
- [ ] Image collection protocol and consent wording.
- [ ] Labelling handbook (taxonomy, uncertainty classes, severity, provenance).
- [ ] Plant-clinic archive access assessed.
- [ ] Weather provider and boundary dataset chosen, licence recorded.
- [ ] Database schema implemented and migrated (`05-data-layer.md`).
- [ ] Data dictionary v1; quality checks for each ingestion batch.
- [ ] Quarantine path for suspicious records.

**Gate 1:** documented permissions for every dataset; reproducible ingestion; label
handbook approved by a pathologist.

### Phase 2 — Platform MVP `[ ]`

- [~] **§5.1 Engineering foundation** — backend/web/mobile scaffolds, CI,
      Alembic baseline, local compose, dev/staging env templates, structured
      logging, OpenAPI/error contract and `../TEST-MATRIX.md`. Mobile
      `flutter analyze` and `flutter test` pass locally (Flutter 3.47.9); no APK
      or device run yet. Gate 1 is **not met**; foundation-only work proceeds
      under an explicit user instruction recorded 2026-11-06 and adds no schema
      or feature behaviour.
- [~] Auth, roles, consent (`03-auth-and-roles.md`) — backend §5.2 slice implemented
      in memory (OTP, staff MFA, five roles, consent versioning, privacy requests,
      audited admin views/exports). Durable persistence, demo-route auth and the
      D10/D11-dependent behaviour remain open.
- [ ] Mobile context + capture + quality feedback + offline queue (`02-...`).
- [ ] Observation API with idempotency and presigned uploads.
- [ ] Web frontend shell + mobile app shell consuming the same `/v1` API.
- [~] Conversational capture: `conversations` module + chat on web
      (`08-conversational-capture.md`). **Backend + web slice implemented and
      persisted** (Alembic `0002_chat_persistence`): validated image upload and
      owner-scoped preview, demo quality gate, pluggable assessment engine
      (`demo` default; unknown values fail closed), idempotent turns, review
      requests, and the web thread/composer/card. Mobile, real inference, auth
      scoping, object storage and the presigned-URL pipeline remain open.
- [~] Chat reply contract (`assessment`, `abstained`, `unsupported_crop`, `queued`, `failed`,
      `review_requested`) and chemical-content validator. Implemented: `assessed`,
      `abstained` and `failed` states plus persisted `review_requested`; `queued` and
      `unsupported_crop` remain open. The `chat-safety-0.1` validator is built and
      applied to chat and video summaries.
- [~] Video reading (`09-video-reading.md`, added to v1 by explicit user instruction).
      **Backend machinery implemented and demo-labelled** (Alembic
      `0003_video_persistence`): bounded MP4/MOV/WebM upload, deterministic frame
      sampling, per-frame quality gate, `demo-motion-0.1` motion-region detector,
      `bytetrack-lite-0.1` tracker, per-frame photo assessments and a template-only,
      non-diagnostic summary. Chat-composer integration on web/mobile, a real detector
      (D15), retention (D14) and calibration remain open.
- [ ] Expert review queue and decision flow (`04-expert-review.md`).
- [ ] Audit trail for reviews, roles, exports and chat events.
- [ ] Admin config for crops, targets, geographies.
- [ ] End-to-end test: report → upload → review, including airplane mode.
- [~] End-to-end test: chat image → structured reply on web and mobile, retry idempotent.
      Web + API path verified (14 backend tests and a live upload → demo assessment →
      review smoke); mobile path and browser automation remain open.

**Gate 2:** a report can be captured offline, synced once, reviewed, and audited, on a
low-end device; chat image → assessment works on web and mobile. No predictive model
required; any demo reply is labelled.

### Phase 3 — Image AI `[ ]`

- [ ] Quality gate model (blur, exposure, resolution, no-plant).
- [ ] Field-image baseline; public data used for pretraining only.
- [ ] Group-held-out field test set frozen before model selection.
- [ ] Calibration on a dedicated split (temperature scaling) and the D8 abstention decision function (`τ_c`, margin, entropy, OOD) chosen on validation.
- [ ] Evaluation report: macro F1, per-class recall, ECE/Brier, abstention rate, OOD on held-out classes, subgroups; D8 floors pre-registered before the test set is opened.
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

**Gate 4:** the D7 event definition, label eligibility rule, sentinel-panel membership and
visit schedule are fixed and frozen before the test season; the D8 forecast floors are
pre-registered and **met** on sentinel-panel negatives; the D9 coverage, freshness and
suppression values are recorded and approved; the forecast is reproducible from a stored
snapshot; the no-score path is verified against those values; the map never merges reports and
predictions.

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
| Documentation | `[x]` | Keep in sync with decisions |
| Blueprint coverage | `[x]` | Chapter map maintained in `../README.md` |
| Decisions | `[?]` | Resolve D1–D6 with local experts |
| Data acquisition | `[ ]` | Identify archive partners; draft MoU |
| Labelling | `[ ]` | Draft handbook after D1 |
| Backend | `[~]` | Health, problem-details errors, JSON logging, Alembic baseline + `0002_chat_persistence` + `0003_video_persistence`, compose; persisted demo chat (uploads, demo quality gate, demo engine, optional OpenAI-compatible adapter, review requests); demo-labelled video-reading pipeline; §5.2 identity slice in memory. Next: configure and validate a live provider (needs the Gate 1 exception, D1/D8 and the key), durable identity persistence and route auth |
| Mobile | `[~]` | Flutter shell committed; **unverified** — no SDK locally; CI analyze/test job defined |
| Web | `[~]` | Next.js desktop shell in `frontend/` with persistent section sidebar, dashboard and honest locked/not-available routes; typecheck, lint, build and live smoke pass (2026-11-06) |
| Chat | `[~]` | Spec 08 + persisted demo chat backend and web surface (upload → quality gate → demo/OpenAI-compatible engine → review); mobile shell only. Real assessment waits on Phase 3, D8 and a live key |
| Video | `[~]` | Spec 09 + backend machinery (bounded decode/sampling, per-frame quality gate, `demo-motion-0.1`, `bytetrack-lite-0.1`, per-frame assessments, non-diagnostic summary, append-only readings). No trained detector (D15), no chat-composer UI and no retention job (D14) |
| Image ML | `[ ]` | Baseline on public data for pipeline only |
| Forecast | `[ ]` | Implement rules baseline after D1/D2 |
| MLOps | `[ ]` | Registry table design in data layer |
| Security/privacy | `[ ]` | Threat model before Phase 2 exit |
| Pilot ops | `[ ]` | Site list and verification capacity after D3 |

---

## 4. Decisions (blocking)

Record: decision, options, consequence, owner, date. Do not delete history.

Every decision carries **one named accountable owner** and a **`Needs by` date tied to a
phase gate**. A decision with neither cannot be counted as answered, and Gate 0 cannot
close while any remain open. Where a decision needs a number that the repository is not
entitled to invent (R6), the decision must still define *who sets the number, from what
measurement, before which gate* — the rule for setting the value is itself the decision.

### D1 — Crop + targets + zone `[?]`

| Option | Consequence |
|---|---|
| Potato late blight | Validated weather model exists (BLITECAST/SimCast); forecast credible on day one; narrow advisory |
| Tomato late blight / early blight / leaf curl | More targets, more public data, weaker forecast baseline for non-blight targets |
| Rice blast / BLB / brown spot | Large farmer base, harder image data, blast weather models exist |

Recommended default: **potato late blight**, one zone, plus healthy + abiotic look-alike +
unknown. Final choice requires local economic and partner input.
**Owner:** Product lead + agronomist. **Needs by:** Gate 0 (target 2026-11-20).

### D2 — Nowcast or 7-day outlook `[?]`

| Option | Consequence |
|---|---|
| Nowcast (last 10 days) | No historical outcome data needed; more accurate; still actionable |
| 7-day outlook | Needs validation against outcomes; risk of overclaiming in year one |

Recommended default: **nowcast for v1**, add outlook when a season of verified outcomes
exists. **Owner:** Agronomist + ML lead. **Needs by:** Gate 0.

### D3 — Verifier, capacity, SLA `[?]`

| Option | Consequence |
|---|---|
| Extension-worker-first | Scales; needs training and triage rules; pathologist for escalation |
| Pathologist-first | Higher label quality; immediate backlog; not viable at volume |

Recommended default: **extension-first**, pathologist escalation, published SLA and
workload cap. **Owner:** Programme lead + partner. **Needs by:** Gate 0.

### D4 — Owning/paying institution `[?]`

Options: government agriculture department, cooperative/FPO, NGO programme, crop insurer.
Recommended default: **grant/NGO-funded pilot → cooperative or insurer operations**.
Input-company funding for the advisory layer is rejected on trust grounds.
**Owner:** Product lead. **Needs by:** Gate 0.

### D5 — Primary outcome metric `[?]`

Recommended default: **median lead time from first farmer report to verified expert
confirmation**, versus the existing advisory baseline, pre-registered. Secondary:
prioritisation accuracy, false-alert burden.
**Owner:** Product lead + evaluator. **Needs by:** Gate 0.

### D6 — Legal position on advisory content `[?]`

Options: non-chemical only (recommended), approved chemical content with legal sign-off
(not recommended for v1), no advisory in v1 (weakens product).
Recommended default: **non-chemical + escalation**, legal review before pilot.
**Owner:** Programme lead + legal. **Needs by:** Gate 0 (legal sign-off before Gate 5).

### D7 — Forecast event, negative class and label eligibility `[x]`

**Accepted 2026-11-06.** Sentinel-panel absence sampling; `probable` is eligible with an
evidence tier.

**Negative class.** A fixed sentinel panel of monitored field points is defined per supported
area before the season and visited on a pre-registered schedule by extension workers or
partners. At each visit the visitor records observed presence or absence of the supported
target using the same diagnostic criteria as case verification. A visit yields a **verified
negative** only if all of these hold: the visit falls inside the label window; the point is on
the supported crop in the supported area; the visit was scheduled in advance, not triggered
by a report; and the D9 coverage gate passed for that area and window. `no visit`, `no
report`, `unresolved` and `needs_visit` are never negatives.

**Event.** First evidence-eligible case of the target in the spatial unit within the event
window. The event date is the earliest observed/onset date recorded. The exact outcome (first
case, incidence threshold or escalation) still follows D1/D5, but the eligibility rule is
fixed: a case enters features only if `verified_at <= cutoff` and its event date is
`<= cutoff`. `confirmed` and `probable` are eligible; `probable` carries its evidence tier as
a lower-confidence flag. `unverified`, `needs_visit`, `duplicate`, `unresolved` and `rejected`
are never eligible.

**Training versus evaluation.** Features may be trained on presence-only data, but that is a
positive-unlabelled design: PR-AUC, precision/recall, Brier and ECE are reported **only** on
the sentinel panel, which supplies real negatives. If the panel is below the D8 minimum
sample for a stratum, the metric is reported as underpowered and is not used for a gate. No
metric is ever computed by treating an unvisited area as negative.

**Blinding.** The primary review records the label before seeing model candidates or the
forecast at report time; both are revealed only after the decision is stored. A double-read
subset is labelled independently and inter-rater agreement is reported; its size and threshold
are set under D8.

**Label maturity.** A season is not frozen as test data until its label window has closed and
the review backlog for that window is cleared. Right-censored recent cases are excluded from
the frozen set, never labelled negative.

**Consequence — capacity:** the panel and its visit schedule are a D3 commitment. Without
them the forecast track has no negative class and must fall back to presence-only, in which
case discrimination and calibration are not reported at all.

**Owner:** ML lead + agronomist + pathologist + field ops. **Recorded:** 2026-11-06;
frozen before Gate 4.
**Blocks:** `06-forecast-and-risk-map.md` §2/§9/§11, `04-expert-review.md` §3/§6,
`05-data-layer.md` §4.4, `phase-plan.md` §7.1.

### D8 — Abstention rule and numeric acceptance floors `[x]`

**Accepted 2026-11-06: the decision function, the operating posture, the calibration and OOD
requirements, the override policy and the floor-setting process. The floor *values* are not
invented here — they are measured and pre-registered before the frozen test set is opened, as
described below.**

#### Decision function — image assessment

Applied only after the server quality gate passes:

1. Calibrated class probabilities (or the raw decision score when calibration is not
   approved for display).
2. Top-1/top-2 margin and normalised entropy.
3. An explicit out-of-distribution score computed on embeddings or energy, with its threshold
   fitted on held-out classes.

Abstain with a machine reason code if **any** of these holds: the top candidate's calibrated
probability is below its class threshold `τ_c`; the margin is below `m`; entropy is above
`h`; the OOD score is above `ood_max`; the crop is unsupported; the quality gate fails (a
separate upstream state). Return up to three candidates only when none hold.

`τ_c`, `m`, `h` and `ood_max` are stored per prediction with the model version. Per-class
`τ_c` is required; a single global threshold is not sufficient for classes of unequal
prevalence.

#### Operating posture

**Safety-first.** Per-class recall floors take precedence over coverage. Among operating
points that satisfy the recall and OOD constraints, choose the one that maximises the share
of images assessed. Never trade a recall floor for coverage. A model that abstains on
everything fails Gate 3 — the coverage floor exists precisely to prevent that.

#### Calibration

Probabilities used by the decision function are calibrated with **temperature scaling** on a
dedicated calibration split, separate from the validation split used for model selection and
from the frozen test set. Isotonic calibration is permitted only where the sample size
supports it. ECE is a diagnostic, not a fitting method. Report reliability diagram, Brier
score and ECE on the frozen test set.

If the data cannot support a separate calibration split, calibration is **not approved**:
the UI shows qualitative bands only, no percentage, and no probability-derived claim. The
model may still abstain on its raw score.

#### Out-of-distribution

A supervised `unknown` class is not open-set detection: it only recognises unknowns present
in training. D8 therefore requires a separate OOD score evaluated on **held-out classes** —
unknown-vs-known AUROC and false-accept rate at the shipped threshold. Both are gate
metrics, not diagnostics.

#### Numeric floors — measured, never invented

Two floor sets, each pre-registered in this section, timestamped and committed **before** the
frozen test set is opened:

**Image floors**
- Minimum per-class recall at the shipped threshold.
- Maximum overall and per-class abstention rate.
- Minimum share of quality-passing images assessed.
- Maximum ECE (only if calibration is approved).
- Maximum OOD false-accept rate on held-out classes.
- Minimum top-3 containment for supported classes.

**Forecast floors**
- Minimum share of area-days carrying a scored band (not `insufficient_data`).
- Maximum `insufficient_data` rate.
- Minimum lift over the climatology / naive baseline on the D7 evaluation.
- Maximum Brier and calibration error on sentinel-panel negatives.
- Results broken down by coverage stratum.

Procedure:
1. Freeze dataset, split and model versions.
2. On validation/calibration data only, measure risk–coverage curves per class and subgroup
   and the baseline lift.
3. The evaluator and product lead write the floors and the chosen operating point into this
   section, with a timestamp and commit, under D7's anti-leakage rules.
4. Open the frozen test set once and report at the shipped threshold.
5. Any floor that is not met means the model is **not approved** and Gate 3 (or Gate 4 for
   forecast) fails. Thresholds may not be retuned after the test set is opened; a retrain
   requires a new pre-registration.

Floors set after seeing test results are void.

#### Override policy

- There is **no user-facing control that changes a model output**. An abstained prediction
  stays abstained in the record.
- A reviewer may still verify a report manually through the normal review flow. That decision
  is separate, audited, and never rewrites the prediction row or counts as an assessed image
  in coverage.
- `confirmed` remains pathologist-only. Extension workers may escalate; agronomists and
  admins cannot verify.
- Every manual decision records actor, role, timestamp, reason and the model state it
  replaced, and appears in the audit log.
- Manual labels are not fed back as ground truth for model evaluation without D7's labelling
  protocol and evidence tier; doing so would import confirmation bias into the test set.

**Owner:** ML lead + product lead + evaluator. **Recorded:** 2026-11-06.
**Floor values:** not yet recorded — Gate 3 and Gate 4 cannot close until the relevant set is
pre-registered and met.
**Blocks:** Gate 3, Gate 4, `ml-models.md` §6, `01-design-system.md` confidence bands,
`02-reporting-and-capture.md` FR-02-25, `05-data-layer.md` `image_predictions`.

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

### D13 — `agronomist` as a fifth role `[x]`

**Accepted 2026-11-06.** `agronomist` is a fifth RBAC role, not an attribute on
`pathologist` and not an external approver who never logs in.

**Why:** advisory approval was impossible to perform as specified — the role matrix had no
agronomist column, yet `07-advisory-and-alerts.md` required a named agronomist as author and
a second qualified approver, and `06-forecast-and-risk-map.md` required agronomist threshold
approval. `update.md:38` also makes expert capacity the binding constraint, so a design that
needed two pathologists (one to author, one to approve) was unstaffable.

**What `agronomist` can do:** author and approve advisory content; approve risk bands and
threshold changes as second approver; read area queue, case evidence and map layers
read-only.

**What it cannot do:** set verification status, correct labels, create or upload
observations, manage users, export, or read the audit log. Author ≠ approver is enforced per
record (`author_id != approver_id`), so one account holding both roles still cannot
self-approve.

**Consequence — capacity:** the programme must staff at least **two** qualified accounts
(any mix of `agronomist` and `pathologist`) before any advisory can be published. With one,
publication is blocked. This is tracked under D3 and R-03, not resolved by relaxing the rule.

**Owner:** Product lead + programme lead. **Recorded:** 2026-11-06.
**Implemented in:** `03-auth-and-roles.md` §1–§4, §10; `PRD.md` §4.2; `04-expert-review.md`
§2; `05-data-layer.md` §4.1; `07-advisory-and-alerts.md` §2–§3; `phase-plan.md` §5.2.

### D14 — Video retention and deletion window `[?]`

Short clips are stored under `APP_MEDIA_ROOT` so a reading can be reproduced.
Decide the retention window, whether the source clip or only the assessed frames
are kept, and the deletion path (soft delete plus object-storage lifecycle). Until
decided, no retention job exists; `video_uploads.deleted_at` is present so a job
can be added without a schema change. **Owner:** Product lead + privacy lead.
**Needs by:** before any real user clip is stored. **Interim rule:** do not store
real farmer footage; synthetic/demo clips only.

### D15 — Detector/tracker model and validation protocol `[?]`

`demo-motion-0.1` is a frame-difference heuristic and `bytetrack-lite-0.1` is a
dependency-light reimplementation, not the official ByteTrack package. Replacing
them needs an approved crop/target taxonomy (D1/D2), a labelled video dataset, a
pre-registered evaluation protocol and the D8 decision function. **Owner:** ML lead.
**Needs by:** Phase 3. **Interim rule:** every video reading stays `is_demo=true`,
`calibrated=false` and `requires_review=true`; a tracker id is never a pest
identity.

---

## 5. ADR log

| ID | Decision | Status | Date |
|---|---|---|---|
| ADR-001 | Modular monolith over microservices | Accepted | 2026-11-06 |
| ADR-002 | FastAPI + SQLAlchemy/Alembic as single schema authority (no Prisma) | Accepted | 2026-11-06 |
| ADR-003 | Web portals are API-only clients | Accepted | 2026-11-06 |
| ADR-004 | Rules-based forecast before ML | Accepted | 2026-11-06 |
| ADR-005 | ONNX Runtime CPU inference for pilot | Proposed | 2026-11-06 |
| ADR-006 | Flutter capture + SMS/WhatsApp delivery | Proposed | 2026-11-06 |
| ADR-007 | Full-stack delivery: one API, web app and mobile app are all in scope | Accepted | 2026-11-06 |
| ADR-008 | Chat is a `conversations` wrapper over photo assessment, not a new model or generative diagnosis | Accepted | 2026-11-06 |
| ADR-009 | The Next.js web app lives in `frontend/` (source documents say `web/`); the folder name follows the existing repository layout | Accepted | 2026-11-06 |
| ADR-010 | Video reading is a capture format for the existing photo-assessment pipeline, not a new model or video-level diagnosis; the detector/tracker seam ships demo-labelled | Accepted | 2026-11-06 |

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
| R-20 | Video tracker output read as pest identification or a video-level diagnosis | M | H | Motion-region naming; demo-only versions; per-frame assessments only; template summary; `requires_review=true`; no video-level label | Product + ML lead | Open |

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
| 2026-11-06 | **D13 accepted:** `agronomist` added as a fifth role (advisory author/approver, risk-band approval, read-only area; cannot verify cases). Updated the RBAC matrix, MFA list and acceptance criteria in `03-auth-and-roles.md`; role lists in `PRD.md`, `phase-plan.md` and `05-data-layer.md`; review-role table in `04-expert-review.md`; advisory author/approver rules in `07-advisory-and-alerts.md`. Publication now requires two qualified accounts (D3 capacity). |
| 2026-11-06 | **D7 accepted:** forecast negatives come from a pre-registered sentinel panel, not from missing reports; `probable` is eligible with an evidence tier; as-of cutoffs, label-maturity embargo and blinded primary review are mandatory. Updated forecast task/evaluation/edge cases, review flow and requirements, sentinel tables, label-eligibility invariants in TRD/architecture/workflow rules, and Phase 4 plan. Discrimination/calibration are reported only on sentinel negatives; panel below the D8 minimum is marked underpowered. |
| 2026-11-06 | **D8 accepted:** safety-first abstention function (per-class `τ_c`, margin, entropy, explicit OOD, quality/crop gates), temperature scaling on a dedicated calibration split, OOD evaluated on held-out classes, and no user-facing override of a model output. Image and forecast floors are pre-registered before the frozen test set is opened; floors set after opening are void. Updated `ml-models.md`, `phase-plan.md` §6.4–6.5 and Gate 3, design-system confidence/abstain states, reporting requirements and acceptance, `image_predictions` schema/constraints (`decision_thresholds`, `ood_score`, `calibration_version`), TRD invariants and forecast evaluation/acceptance. Floor values remain unrecorded pending measurement. |
| 2026-11-06 | Reconciled the partner-added `database/` Phase-1 artifacts with D7/D8/D10/D13: forecast negatives come only from sentinel visits (image healthy/hard negatives are not forecast negatives); added the D8 prediction-decision table and D7 sentinel site/visit fields; verification rows now name the pathologist, not the agronomist; retention/controller references now point to D10. |
| 2026-11-06 | Phase 2 §5.1 engineering foundation: FastAPI app factory with RFC 7807 problem details, request-id middleware and JSON logs; SQLAlchemy session + Alembic `0001_baseline`; Next.js web client in `frontend/` (typecheck, lint and build pass); Flutter shell in `mobile/` (committed, unverified — no SDK); compose with PostGIS, API and web images; env templates for dev/staging; CI for backend, web, mobile, compose and image builds; `TEST-MATRIX.md`. No feature work; Gate 1 remains unmet. Added ADR-009. |
| 2026-11-06 | Web chat surface (Phase 2 §5.7, demo backend): `/chat` conversation list and `/chat/[conversationId]` thread; structured assessment card with assessed/abstained/unsupported/failed states; metadata-only image picker and drag-and-drop; idempotent retry and conversation delete; honest not-available routes for `/outlook` and `/review`. Added `design/tokens.json` and an application shell with mirrored CSS variables. Typecheck, lint, production build and live smoke pass. Upload/media, real inference, auth scoping and the mobile surface remain open; no gate is claimed. |
| 2026-11-06 | Desktop web shell: persistent section sidebar (Overview, Photo assessment, Area outlook, Review queue) with active-state marker and skip link; desktop dashboard with platform status and separate-output cards; collapses to a horizontal nav below 1024px and single-column grids below 640px; locked `/review` boundary page with no fabricated cases; `/outlook` now reads the five independent `/v1/map/layers/*` endpoints and shows each layer's own state (`map_not_configured` is explicit, never a merged risk value). Typecheck, lint, production build and live route smoke pass. |
| 2026-11-06 | Reconciled `../../IMPLEMENTATION-CHECKLIST.md` against the repository: added a work log for the §5.1 foundation, §5.7 web chat surface, `database/` governance artifacts and test evidence; ticked only evidence-backed items (architecture choices, doc reconciliation, rebuilt venv, JSON logging/request IDs/problem details, frontend build/lint/typecheck, production docs restriction). `.gitignore` stays unticked because `dist/` is missing; all auth, readiness, domain-schema, media, model, forecast, alert, map, admin, audit and i18n items remain open. Verdict remains **NOT COMPLIANT**; Gate 0 and Gate 1 are unmet. |
| 2026-11-06 | Verified the Flutter client locally after installing Flutter 3.47.9 (stable, Dart 3.13.7): `flutter pub get` resolved 30 packages, `flutter analyze` reported no issues, `flutter test` passed the single widget test. Updated `TEST-MATRIX.md` FND-11 to Verified (analyze + test), the mobile README, `AGENTS.md` §5, PRD/TRD status lines and `IMPLEMENTATION-CHECKLIST.md` W-11. Still open: `android/`/`ios/` runners, an APK build, a device/emulator smoke and a recorded CI run. No gate is claimed. |
| 2026-11-06 | Phase 2 §5.2 identity backend slice: phone OTP for farmers, provisioned staff accounts, five-role deny-by-default dependencies, password+TOTP login, rotating refresh tokens with family revocation, versioned consent capture, privacy requests/self-export/soft deletion, credential-only retention job, and audited role changes, admin record views and exports. 64 new tests; full backend suite 294 passed. Deliberately **not** done: durable SQLAlchemy/Alembic persistence, authentication of the existing demo chat/assessment/advisory/map routes, real SMS/email providers, password reset, Argon2id (stdlib `scrypt` used instead), and D10/D11-dependent retention/on-behalf/offline behaviour. Gate 1 remains unmet and no gate is claimed. |
| 2026-11-06 | Reconciled the chat ORM with the merged domain ORM: `app/db/base.py` now provides the shared `UTCDateTime`/`utc_now`/`new_id` helpers; `app/db/models.py` re-exports the chat models (`Conversation`, `Message`, `MessageEvent`, `ImageUpload`, `ChatReviewRequest`) and keeps the observation-review `ReviewRequest` on `review_requests`; the chat review table is `chat_review_requests` (Alembic `0002_chat_persistence`); `alembic/env.py` loads `app.db.models`. Verified: both ORM modules import together, `Base.metadata.create_all` creates 48 tables on SQLite, `alembic history`/offline SQL are unchanged in chain, full suite 294 passed, and the live upload → assessment → review smoke passed on a fresh database. |
| 2026-11-06 | Persisted chat slice (Phase 2 §5.7): Alembic `0002_chat_persistence` (`conversations`, `messages`, `message_events`, `image_uploads`, `chat_review_requests`); `POST/GET /v1/uploads` with a JPEG/PNG/WebP allow-list, 10 MB ceiling, real decode, SHA-256 and a versioned demo quality gate; pluggable `AssessmentEngine` seam with a deterministic, labelled `DemoAssessmentEngine` (`demo-chat-0.1`) and fail-closed unknown configuration; idempotent turns; `POST …/messages/{id}/review`; web composer now uploads first and references `upload_id`, renders the stored preview, quality flags and review status. 14 new chat tests; full suite 294 passed. Live smoke (uvicorn + SQLite + `next start`) passed upload → assessed demo reply → persisted review → preview byte-match → 415 rejection. PostgreSQL/Alembic apply was not run (Docker daemon unavailable); real inference is still blocked on the API key and governance. |
| 2026-11-06 | Reconciled a force-pushed `main`: a collaborator's line (`697944d`, diverged at `611aa48`) added a parallel backend, Phase-0 docs and ADRs. Merged it while keeping this line's tested backend for overlapping paths (`app/api`, `app/core`, `app/db`, conversations, identity). The collaborator's new Phase-0 documents, ADRs, `backend/backend/*` vertical slice and non-conflicting files are retained; its superseded `app/*` implementations remain in history but are not wired. Removed the committed `backend/var/ps03.db` artifact. Backend suite re-run after the merge: 294 passed. |
| 2026-11-06 | Added the chat content-safety gate (CHAT-10, R5/R18): the deterministic, fail-closed `chat-safety-0.1` validator checks the reply text, assessment reason and candidate display names before storage. A blocked reply is stored as `failed` with `reason_code`/`error_code` `unsafe_content_blocked`, no candidates and `request_review`; a `validator_rejected` message event records the validator version and rule categories without the unsafe text. 19 validator unit tests and 3 API safety-gate tests; full backend suite 316 passed. A live API smoke on a fresh SQLite database re-ran upload → assessed `demo-chat-0.1` reply → persisted review → idempotent replay → preview byte-match → `415` rejection with the validator in the path. |
| 2026-11-06 | Added the optional OpenAI-compatible vision engine behind the `AssessmentEngine` seam (`APP_CHAT_ENGINE=openai_compatible`): the adapter posts a downscaled JPEG plus `APP_CHAT_LABELS` to `{APP_CHAT_BASE_URL}/chat/completions`, accepts JSON-only candidates, drops unknown labels and renders reply text from fixed templates. Missing key/model/labels, timeouts, HTTP failures and malformed output are explicit `failed` states; a model abstention is `abstained`/`model_abstained`. `is_demo` stays true until `APP_CHAT_LABELS_APPROVED=true`, so no D1/D2 taxonomy is invented in code. `httpx` moved to runtime dependencies; compose passes the chat variables and mounts a media volume. 19 engine tests and 1 API wiring test; full suite 336 passed. Verified with a mock transport and a live uvicorn run against a local OpenAI-compatible HTTP stub: upload → `assessed`, `is_demo=false`, `model_version=stub-vision-1`, one approved candidate, template text, persisted review and 2 messages. No real vendor call was made. |
| 2026-11-06 | Added the demo-labelled video-reading machinery (`09-video-reading.md`, added to v1 by explicit user instruction; supersedes the video exclusions in specs 02 §11 and 08 §3.2). Bounded MP4/MOV/WebM upload with size/duration/dimension ceilings, deterministic frame sampling, per-frame quality gate, `demo-motion-0.1` frame-difference detector, `bytetrack-lite-0.1` tracker, at most three per-frame photo assessments through the existing `AssessmentEngine`, a template-only non-diagnostic summary and append-only `video_readings` (Alembic `0003_video_persistence`). Abstention (`no_stable_region`, `insufficient_usable_frames`) and explicit `failed` states; `chat-safety-0.1` runs on the summary; every reading is `is_demo=true`, `calibrated=false`, `requires_review=true`. 17 new tests; full backend suite 353 passed. Added ADR-010, R-20 and open decisions D14/D15. Deliberately **not** done: a trained detector, retention/deletion (D14), chat-composer video UI, calibration and a live PostgreSQL apply. |

---

## 8. Next five actions

1. Run a decision workshop for D1–D6; record outcomes in §4.
2. Draft the data acquisition plan (partner MoUs, archive access, collection targets).
3. Draft the labelling handbook for the chosen crop and target list.
4. Draft the pilot protocol (sites, silent phase, comparison design, pre-registered metric).
5. Finish mobile verification (generate `android/`/`ios/` runners, build a debug APK,
   device smoke) and build both container images; then expand only after Gate 0,
   starting with identity + observations + audit + `conversations`.

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
| Technical | Image macro F1, per-class recall, calibration, abstention rate; forecast PR-AUC, Brier, calibration on sentinel-panel negatives only (underpowered below the D8 minimum); latency |
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

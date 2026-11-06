# Progress tracker

**Single place to see where the project is, what is decided, and what comes next.**
Update this file in the same change as any scope, schema, API or decision change.

**Last updated:** 2026-11-06
**Current phase:** Phase 0 — Discovery (documentation complete, decisions open)

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
- [ ] Crop calendar and epidemic window documented for the pilot area.

**Gate 0:** D1–D6 answered and recorded in §4. No code that depends on them.

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

- [ ] Auth, roles, consent (`03-auth-and-roles.md`).
- [ ] Mobile context + capture + quality feedback + offline queue (`02-...`).
- [ ] Observation API with idempotency and presigned uploads.
- [ ] Expert review queue and decision flow (`04-expert-review.md`).
- [ ] Audit trail for reviews, roles and exports.
- [ ] Admin config for crops, targets, geographies.
- [ ] End-to-end test: report → upload → review, including airplane mode.

**Gate 2:** a report can be captured offline, synced once, reviewed, and audited, on a
low-end device. No model required.

### Phase 3 — Image AI `[ ]`

- [ ] Quality gate model (blur, exposure, resolution, no-plant).
- [ ] Field-image baseline; public data used for pretraining only.
- [ ] Group-held-out field test set frozen before model selection.
- [ ] Calibration + abstention thresholds chosen on validation.
- [ ] Evaluation report: macro F1, per-class recall, ECE, abstention rate, subgroups.
- [ ] ONNX export, registry entry, versioned serving.
- [ ] Result card with top-3, confidence band, quality flags, escalation.

**Gate 3:** performance reported at the shipped abstention threshold on a field-only
test set, with sample counts; abstention works on hard negatives.

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

**Gate 4:** forecast is reproducible from a stored snapshot; no-score path verified;
map never merges reports and predictions; thresholds approved by agronomist.

### Phase 5 — Pilot `[ ]`

- [ ] Site selection and control/matched design documented.
- [ ] Silent phase running (predictions not shown).
- [ ] Comparison with field observations; false alerts and missed events logged.
- [ ] Limited alert phase with approved templates and escalation owners.
- [ ] Usability and comprehension rounds with farmers and extension workers.
- [ ] Lead-time measurement against baseline.
- [ ] Weekly review cadence and issue log.

**Gate 5:** silent-phase evidence reviewed; alert response workflow staffed; no unresolved
safety issue. Pilot timed to the epidemic season.

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
| Backend | `[ ]` | Scaffold after Gate 0 |
| Mobile | `[ ]` | Prototype capture flow after Gate 0 |
| Web portals | `[ ]` | Prototype queue + map shell |
| Image ML | `[ ]` | Baseline on public data for pipeline only |
| Forecast | `[ ]` | Implement rules baseline after D1/D2 |
| MLOps | `[ ]` | Registry table design in data layer |
| Security/privacy | `[ ]` | Threat model before Phase 2 exit |
| Pilot ops | `[ ]` | Site list and verification capacity after D3 |

---

## 4. Decisions (blocking)

Record: decision, options, consequence, owner, date. Do not delete history.

### D1 — Crop + targets + zone `[?]`

| Option | Consequence |
|---|---|
| Potato late blight | Validated weather model exists (BLITECAST/SimCast); forecast credible on day one; narrow advisory |
| Tomato late blight / early blight / leaf curl | More targets, more public data, weaker forecast baseline for non-blight targets |
| Rice blast / BLB / brown spot | Large farmer base, harder image data, blast weather models exist |

Recommended default: **potato late blight**, one zone, plus healthy + abiotic look-alike +
unknown. Final choice requires local economic and partner input.
**Owner:** Product lead + agronomist. **Needed by:** Gate 0.

### D2 — Nowcast or 7-day outlook `[?]`

| Option | Consequence |
|---|---|
| Nowcast (last 10 days) | No historical outcome data needed; more accurate; still actionable |
| 7-day outlook | Needs validation against outcomes; risk of overclaiming in year one |

Recommended default: **nowcast for v1**, add outlook when a season of verified outcomes
exists. **Owner:** Agronomist + ML lead.

### D3 — Verifier, capacity, SLA `[?]`

| Option | Consequence |
|---|---|
| Extension-worker-first | Scales; needs training and triage rules; pathologist for escalation |
| Pathologist-first | Higher label quality; immediate backlog; not viable at volume |

Recommended default: **extension-first**, pathologist escalation, published SLA and
workload cap. **Owner:** Programme lead + partner.

### D4 — Owning/paying institution `[?]`

Options: government agriculture department, cooperative/FPO, NGO programme, crop insurer.
Recommended default: **grant/NGO-funded pilot → cooperative or insurer operations**.
Input-company funding for the advisory layer is rejected on trust grounds.
**Owner:** Product lead.

### D5 — Primary outcome metric `[?]`

Recommended default: **median lead time from first farmer report to verified expert
confirmation**, versus the existing advisory baseline, pre-registered. Secondary:
prioritisation accuracy, false-alert burden.
**Owner:** Product lead + evaluator.

### D6 — Legal position on advisory content `[?]`

Options: non-chemical only (recommended), approved chemical content with legal sign-off
(not recommended for v1), no advisory in v1 (weakens product).
Recommended default: **non-chemical + escalation**, legal review before pilot.
**Owner:** Programme lead + legal.

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

L = likelihood, I = impact, both H/M/L.

---

## 7. Changelog

| Date | Change |
|---|---|
| 2026-11-06 | Created `docs-context/` and `feature-specs/` from `summary.md`, `totalcontent.md`, `update.md`. v1 scope narrowed per realism audit. Six decisions recorded as open. |
| 2026-11-06 | Aligned the full documentation set to the supplied 55-chapter blueprint. Added `data-foundation.md`, `ml-models.md`, `operations-and-pilot.md`, `roadmap-and-resources.md`, `appendices.md`, and the chapter map in `README.md`. Expanded overview, architecture, UI, code standards, workflow rules and feature specs. No scope decision changed; D1–D6 remain open. |
| 2026-11-06 | Added `phase-plan.md`: a detailed per-phase work breakdown (workstreams, deliverables, exit gates, owners, dependencies and explicit exclusions for Phases 0–6). Linked it from the README, `AGENTS.md`, `project-overview.md` and `roadmap-and-resources.md`. No gate, scope or decision changed. |
| 2026-11-06 | Added `final/PRD.md` and `final/TRD.md`: consolidated product and technical requirements distilled from the operating docs, feature specs and phase plan. No gate, scope or decision changed. |

---

## 8. Next five actions

1. Run a decision workshop for D1–D6; record outcomes in §4.
2. Draft the data acquisition plan (partner MoUs, archive access, collection targets).
3. Draft the labelling handbook for the chosen crop and target list.
4. Draft the pilot protocol (sites, silent phase, comparison design, pre-registered metric).
5. Scaffold `backend/` only after Gate 0, starting with identity + observations + audit.

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
| Ch 11–12 | `../feature-specs/02`–`07`, `code-standards.md` |
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

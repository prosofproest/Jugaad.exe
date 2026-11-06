# Roadmap, resources and risks

**Covers:** blueprint Chapters 50–52 — implementation roadmap, budget and resource planning,
and the risk register.
**Status:** planning baseline. The authoritative phase gates live in
`./progress-tracker.md` §2; this document explains the reasoning behind them.
**Last updated:** 2026-11-06

**Detailed work breakdown:** `./phase-plan.md` expands every phase below into
workstreams, deliverables, exit gates, owners and explicit exclusions.

---

## 1. Implementation roadmap (Chapter 50)

The roadmap is phased so the team establishes trustworthy data and workflows before relying
on complex predictions. Each phase must produce something a real user would use on its own.

### Phase 0 — Discovery

Select crop, targets, geography, stakeholders, event definitions and pilot success measures.
Output: recorded decisions D1–D6 and a documented crop calendar.

### Phase 1 — Data foundation

Secure data access, collect images, define labels, ingest weather, build the database.
Output: documented permissions, reproducible ingestion, approved label handbook.

### Phase 2 — Platform MVP

Deliver mobile reporting, case management, expert portal and the offline queue.
Output: a report captured offline, synced once, reviewed and audited. No model required.

### Phase 3 — Image AI

Train and validate a field-image model with a quality gate and abstention.
Output: evaluation report at the shipped threshold, ONNX export, registry entry.

### Phase 4 — Forecasting

Build the rules baseline, feature pipeline, model, calibration and risk map.
Output: a reproducible forecast from a stored snapshot, with a verified no-score path.

### Phase 5 — Pilot

Run silent evaluation, limited alerts, field verification and usability refinement.
Output: lead-time evidence, false-alert and missed-event log, comprehension findings.

### Phase 6 — Rollout

Complete operational readiness, monitoring, training and controlled expansion.
Output: signed launch-readiness checklist and named operating owner.

**Critical path:** data access and expert annotation. They gate everything downstream.

**Implementation points**

- Do not promise a reliable forecast before enough historical evidence exists.
- Do not start Phase 2 before Gate 0 (decisions resolved).
- Re-estimate at every gate; a slipped data phase shifts the whole plan.

---

## 2. Budget and resource planning (Chapter 51)

Budget depends on geography, crop scope, data availability, staffing and deployment model.
Build cost estimates from a work breakdown structure, not a single technology guess.

| Category | Includes |
|---|---|
| People | Product, engineering, data, ML, agronomy, field collection, QA, support |
| Data acquisition | Field visits, enumerators, expert labelling, laboratory confirmation, licences |
| Infrastructure | Cloud compute, GPU for training, database, storage, maps, monitoring, backups |
| Operations | Connectivity, devices, training, translation, user support, maintenance |
| Risk reserve | Seasonal delays, provider changes, additional data collection |

Guidance from the realism audit:

- Pilot-scale infrastructure is a small share of total cost; people and field data dominate.
- CPU inference is sufficient for MobileNet-class models at pilot scale; GPU is for training.
- NASA POWER / ERA5-Land are free; avoid paid weather providers until resolution demands it.
- A model registry table plus artefact storage is enough; do not stand up a full MLOps stack.

**Cost scenarios:** prepare low, expected and high estimates. Track recurring operating cost
separately from one-time development cost. No cost figure in this document is a committed
number; the approved envelope is recorded in `./progress-tracker.md` once agreed.

**Implementation points**

- Budget the verification network (reviewer time, field visits) explicitly.
- Budget translation and localisation as an engineering task, not a download.
- Hold a risk reserve for a missed season or a provider change.

---

## 3. Risk register and mitigation (Chapter 52)

The main risks are data scarcity, domain shift, look-alike symptoms, uneven reporting, poor
connectivity, false alarms, unsafe advice and partner dependency.

| Risk | Why it matters | Mitigation |
|---|---|---|
| Data scarcity | No verified historical data in year one | Rules baseline + reporting network; state limits honestly |
| Domain shift | Public-data models fail in the field | Field test set; domain adaptation; quality gate |
| Look-alike symptoms | Same visible sign, different cause | Abiotic class; expert review; label handbook |
| Reporting bias | "No reports" read as "no disease" | Coverage as feature and UI; suppression rules |
| Poor connectivity | Reports lost or duplicated | Offline queue; idempotency; stale-cache handling |
| False alarms | Alert fatigue and lost trust | Calibration; cooldown; feedback loop |
| Missed events | Silent failure | False-negative review; escalation path |
| Unsafe advice | Legal and health liability | Approved non-chemical content only; validator; legal review |
| Verification backlog | Verified layer empties | Extension-first triage; SLA; workload caps |
| Partner withdrawal | Pilot stops mid-season | Dual partnerships; data ownership agreed upfront |
| Seasonality | Pilot misses the epidemic window | Calendar-driven planning |
| Privacy breach | Farm and identity exposure | Approximate location; RBAC; audit; DPIA |
| Scope creep | Multi-crop, universal diagnosis | Expansion rule; Gate 0 decisions |

The live register with IDs, likelihood, impact, owner and status is maintained in
`./progress-tracker.md` §6. Review it at every milestone.

**Implementation points**

- Every risk has one accountable owner.
- A mitigation that is a policy note is weaker than one enforced in code.
- Record risk acceptance explicitly; do not let it become invisible.

---

## 4. Resource questions that gate the plan

1. Who funds and owns the service after the pilot? (D4)
2. What is the daily verification capacity and SLA? (D3)
3. What is the legal position on advisory content? (D6)
4. Which provider operates SMS/WhatsApp, and at what per-message cost?
5. Is the pilot timed to the epidemic season?

These are tracked in `./progress-tracker.md` §4 and must be resolved before the phases that
depend on them.

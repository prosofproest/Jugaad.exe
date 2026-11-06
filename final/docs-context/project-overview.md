# Project overview

**Project code:** PS-03 — Agritech & AI
**Working title:** AI-Based Early Pest and Disease Outbreak Prediction Network
**Status:** v1 scope defined, six decisions still open (see `progress-tracker.md`)
**Last updated:** 2026-11-06

---

## 1. One-line definition

An explainable, offline-tolerant decision-support platform that provides per-image crop
symptom triage and geographically localised pest and disease early warning, backed by
expert verification and approved local advisories.

---

## 2. The problem

- Farmers lack timely, reliable, local information about pest and disease threats.
- Reports are scattered across farms, extension offices and plant clinics.
- Expert capacity is limited and unevenly distributed.
- Images alone cannot predict regional outbreaks; weather alone cannot confirm presence.
- No integrated workflow captures observations, triages them cautiously, combines
  contextual data into local risk, and routes uncertain cases to a human.

The operational consequence: a district team does not know where reports are emerging,
whether they are verified, or how much surveillance has actually happened in each area.

### 2.1 Agricultural context

- **Timing matters.** An alert has value only if it arrives early enough to change a
  decision. Delayed recognition lets damage spread and raises response cost.
- **Local context matters.** Variety, planting date, growth stage, irrigation, local weather
  and nearby confirmed cases all change risk. A generic statement cannot guide a farmer.
- **Diagnosis is difficult.** Disease symptoms overlap with nutrient deficiency, water
  stress, heat, chemical injury, insects and physical damage. Lighting, phone quality, leaf
  age and background clutter further complicate image evidence.
- **Therefore** the platform combines visual and contextual evidence, states its limits and
  routes uncertain or high-impact cases to a human.

---

## 3. Vision and mission

**Vision:** a trusted, accessible, locally relevant service that turns fragmented
agricultural observations into useful early awareness.

**Mission:** deliver two distinct forms of intelligence — image-based symptom triage for
an individual plant, and time-bound outbreak risk estimation for a defined crop and
geographic area — connected through shared case management, verified observations and
responsible advisory delivery.

---

## 4. The central design rule

| | Photo assessment | Area outlook |
|---|---|---|
| **Question** | What might be visible on *this* plant? | How likely is *this threat* in *this area* over *this window*? |
| **Unit** | One photo + crop context | Crop × target × geography × horizon |
| **Output** | Candidate classes, quality flags, confidence band, abstention state, model version | Risk band, probability only if calibrated, drivers, coverage, issue/expiry times |
| **Must never claim** | Laboratory confirmation | Confirmed outbreak |

Neither output replaces field inspection or expert diagnosis. The system must be able to
abstain and show insufficient data. A farmer report becomes a regional signal only after
quality checks and human verification.

---

## 5. Users

| Persona | Core need | Primary surface |
|---|---|---|
| Smallholder farmer | Short, local-language, low-data flow with one clear next action; no probability jargon | Mobile capture + SMS/WhatsApp outlook |
| Progressive farmer / farm manager | Crop-cycle history, multiple fields, trends, exportable records | Mobile |
| Extension worker | Fast case review, location + crop context, verification recording, approved advice | Expert portal (web) |
| Plant pathologist | Original image quality, metadata, alternatives, provenance, label correction | Expert portal (web) |
| District administrator | Aggregated map, time filters, coverage, verified trends, alert audit | District dashboard (web) |

v1 optimises for the **extension worker** as the verification bottleneck owner and the
**smallholder farmer** as the primary field user. The pathologist is an escalation role,
not the default reviewer.

### 5.1 Stakeholder map

| Stakeholder | Contribution | What they need from the system |
|---|---|---|
| Farmers | Observations, context, feedback, consent | Fast, local-language triage and one clear next step |
| Extension workers | Verification, field checks, local practice | A triageable queue, location + crop context, approved advice |
| Plant pathologists / agronomists | Taxonomy, labels, thresholds, advisory approval | Original evidence, alternatives, provenance, correction tools |
| Agricultural institutions | Crop calendars, reference data, pilot access | Aggregated, defensible area information |
| Technology and operations team | Platform, data pipelines, models, security, monitoring | Clear requirements, measurable gates, runbooks |
| Programme administrators | Operational ownership, escalation, SLAs | Coverage, backlog, audit and trend visibility |

**Implementation points**

- Maintain a responsibility matrix for collection, verification, alert approval and
  incident response.
- Hold periodic review meetings during the pilot.
- Technical delivery alone cannot establish trustworthy labels or local thresholds.

---

## 6. v1 configuration (the defended scope)

```
Crop:         1 crop (candidate: potato or tomato — decision pending)
Zone:         1 agro-climatic zone / district cluster
Targets:      3–5 conditions + healthy + abiotic look-alike + unknown
Image AI:     lightweight CNN fine-tuned on field data, quality gate,
              abstention, top-3 candidates
Forecast:     validated agronomic weather-risk model (rules first),
              ML overlay only when data supports it
Product:      Flutter capture app for field staff + farmer-facing SMS/WhatsApp outlook
Verification: extension-worker-first; pathologist for escalations only
Geography:    block/mandal level, never farm level
Timeline:     18 months to limited operational alerts
Team:         7–9 people
```

**Key inversion vs the original blueprint:** lead with the reporting and verification
network plus a rules-based risk model; treat the image model as assistive triage. That
produces something useful in month 6 rather than month 18.

---

## 7. In scope for v1

- Account, language preference, consent.
- Crop-cycle and approximate-area setup (unknown values allowed).
- Camera capture, gallery upload, quality feedback, retake.
- Offline save, queued upload, idempotent sync, stale-cache handling.
- Photo assessment with candidate classes, quality flags, confidence band, abstention.
- Area outlook from a versioned, expert-approved weather-risk model.
- Expert review queue with triage, verification states, evidence notes, audit trail.
- Separate map layers: verified reports, unverified reports, modelled risk, coverage.
- Approved non-chemical advisory retrieval with version and expiry.
- Alerts over SMS/WhatsApp with deduplication, cooldown and feedback.
- Admin configuration of crops, targets, geographies, thresholds and alert policy.
- Audit, basic monitoring, model registry, export controls.

## 8. Out of scope for v1

| Deferred | Cut entirely |
|---|---|
| Spatiotemporal deep learning | Generative AI advisory |
| Drone / satellite analytics | Autonomous chemical guidance |
| On-device inference | Farm-level risk precision |
| Multi-language beyond one | Universal all-crop diagnosis |
| Multi-crop | Confirmed-outbreak claims |
| IoT sensors | Public exact farm coordinates |
| RBAC beyond the four defined roles | Automated model promotion |
| Automated retraining | Yield-impact claims without a study design |

**Expansion rule:** add a crop, target or district only when data, expert labels, local
advisory support and evaluation evidence exist. Scope grows by evidence, not by request.

---

## 9. Core use cases

1. **Submit a symptom report** — select crop/field, capture, optional symptom questions,
   receive case reference. Works offline.
2. **Inspect an area outlook** — risk band, horizon, data freshness, drivers, approved
   prevention guidance, coverage status.
3. **Verify a report** — queue, evidence review, status recording, label correction.
4. **Monitor an area** — filter map by crop, target, date, verification status; export
   aggregates; see backlog and coverage.

Each has designed failure paths:

| Failure | Required behaviour |
|---|---|
| Unsupported crop | No assessment; explain supported crops; offer escalation |
| Blurry / poor image | Quality feedback and retake request; do not classify |
| Weather feed stale | `insufficient_data` outlook; never substitute silently |
| No connectivity | Save locally, show queued state, sync later idempotently |
| Expert backlog | Triage by urgency/uncertainty; show backlog in dashboard |
| Forecast expired | Mark cached value stale; do not present as current |

---

## 10. Objectives

**Primary**

1. Mobile workflow for crop context and image reporting.
2. Image quality checks plus multi-class visual triage.
3. Forecast pipeline for selected crop–threat–area–horizon combinations.
4. Separate map layers for reported cases and forecast risk.
5. Approved preventive guidance and expert escalation.
6. Offline capture, queued upload and safe synchronisation.

**Outcome measures** — baselines and targets are set with domain experts *after* the
baseline is measured. No target numbers are committed in this document.

| Level | Metrics |
|---|---|
| Image | Macro F1, per-class recall, calibration (ECE/reliability), abstention rate |
| Forecast | PR-AUC, Brier score, calibration, lead-time distribution |
| Operational | False alerts per area/time, report-to-review time, backlog, sync success |
| User | Task completion, comprehension of uncertainty wording, repeat use, opt-out |
| Equity | Performance and adoption by geography, device and user segment |

**Single most credible metric:** median lead time from first farmer report to verified
expert confirmation, compared with the existing advisory baseline. It is measurable,
meaningful and hard to fake. It must be pre-registered before the pilot.

---

## 11. Constraints and assumptions

- Rural connectivity is unreliable; low-cost Android devices are the target.
- Expert review capacity is the binding operational constraint, not compute.
- Public image datasets (PlantVillage-style) are for pretraining/benchmarking only.
  They must never be used as the validation set.
- Historical outbreak data will be insufficient in year one; a rules baseline is the
  credible forecast, and a nowcast may be more honest than a 7-day outlook.
- The paying/owning institution after the pilot is undecided. This affects deployment
  model and cost ceiling.
- Advisory content is a regulated surface. Legal review is a prerequisite, not a task.
- One full epidemic season is required to evaluate forecast value. A pilot that misses
  the season produces no forecast evidence.

---

## 12. Ethical and legal boundaries

- No laboratory-confirmation or confirmed-outbreak language anywhere in the product.
- No chemical selection, dosage, mixture or waiting-period guidance.
- Approximate location by default; exact coordinates restricted and audited.
- Consent in plain language; documented retention and deletion.
- Human oversight and a correction path for every automated output.
- No PII or small-count-identifiable data in public or shared dashboards.
- No yield or impact claims without a suitable study design.

---

## 13. Key risks (summary)

| Risk | Mitigation |
|---|---|
| Data scarcity | Rules baseline + reporting network; state limits honestly |
| Domain shift (public → field) | Field data collection; evaluate by district, season, device |
| Reporting bias | Surveillance intensity as feature and UI element |
| Verification backlog | Extension-first triage, workload caps, escalation rules |
| False alarms | Calibration, cooldowns, feedback loop |
| Missed events | False-negative review, escalation path |
| Unsafe advice | Approved content only; no autonomous chemical guidance |
| Seasonality | Time the pilot to the epidemic window |
| Partner withdrawal | Dual partnerships; data ownership agreed upfront |

Full register with owners: `progress-tracker.md`.

---

## 14. Open decisions

Six decisions gate the architecture. They are tracked with options and consequences in
`progress-tracker.md` §4:

1. Crop + 3–5 targets + agro-climatic zone.
2. Nowcast or 7-day outlook in v1.
3. Who verifies, daily capacity, and SLA.
4. Paying/owning institution after the pilot.
5. Single primary outcome metric (pre-registered).
6. Legal position on advisory content.

No implementation choice may pre-empt these silently.

---

## 15. Glossary

| Term | Definition |
|---|---|
| Photo assessment | Automated triage of visible symptoms in one image |
| Area outlook | Estimated future risk for target × crop × geography × horizon |
| Calibration | Agreement between predicted probabilities and observed frequencies |
| Abstention | Model declines to answer when evidence is insufficient |
| Data leakage | Training on information unavailable at prediction time |
| Temporal holdout | Evaluation on a later period not used for training |
| Surveillance intensity | Amount of reporting/inspection activity in an area |
| Coverage | Completeness, freshness and representativeness of inputs |
| Model drift | Change in input patterns or performance over time |
| Stale | Past its validity window; must be visually distinct |

---

## 16. Programme shape

The full blueprint spans 55 chapters; v1 is a deliberately narrow slice of it. Planning
detail lives in the linked documents so this overview stays readable.

| Concern | Where |
|---|---|
| Phased roadmap and gates | `progress-tracker.md` §2; detailed work in `phase-plan.md`; rationale in `roadmap-and-resources.md` §1 |
| Budget and resource logic | `roadmap-and-resources.md` §2 |
| Risk register | `progress-tracker.md` §6; rationale in `roadmap-and-resources.md` §3 |
| Team and responsibilities | `operations-and-pilot.md` §5 |
| Testing, pilot, deployment, monitoring | `operations-and-pilot.md` §§1–4 |
| Success metrics and impact evaluation | `operations-and-pilot.md` §6 |
| Demonstration scenario | `operations-and-pilot.md` §7 |
| Appendices and launch gates | `appendices.md` |

**Timeline:** 18 months to limited operational alerts. **Team:** 7–9 people. These are
planning assumptions, not commitments; they are re-estimated at each gate.

---

## 17. Demonstration scenario (summary)

A farmer selects a supported crop and area, photographs a leaf and submits a report. The app
flags blur and requests a retake. A clearer image receives a possible symptom match with
medium confidence. Separately, the area outlook shows moderate risk for a supported target
over the next seven days (illustrative; D2 decides the shipped horizon), with recent weather
and crop stage as drivers. The farmer gets
scouting guidance and can request expert review. The report appears unverified in the expert
queue; an extension worker records a verification status; the dashboard updates the
verified-report layer without merging it with the forecast layer.

All demonstration data is synthetic and labelled `is_demo`. Fabricated predictions are never
presented as real local warnings.

---

## 18. Future enhancements

- Additional crops and target organisms after data readiness.
- On-device inference for selected models.
- Satellite or drone observations where validated.
- IoT sensors for local microclimate where economically justified.
- Advanced spatiotemporal forecasting after sufficient longitudinal data.
- Interoperability with institutional agricultural information systems.

Expansion happens by evidence: a new crop, target or district is added only when data,
expert labels, local advisory support and evaluation evidence exist.

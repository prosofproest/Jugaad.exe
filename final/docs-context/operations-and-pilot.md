# Operations, testing and pilot

**Covers:** blueprint Chapters 45–49 and 53–55 — testing strategy, pilot design, deployment
and infrastructure, monitoring and model maintenance, project team, success metrics and
impact evaluation, demonstration scenario, and conclusion/future enhancements.
**Status:** operating plan for the pilot. Dates, capacities and thresholds are not
committed here; they live in `progress-tracker.md`.
**Last updated:** 2026-11-06

---

## 1. Testing strategy (Chapter 45)

Testing covers software, data, models, user experience and field operations. A working
prototype is not ready for deployment until its failure modes are understood.

| Layer | What it proves |
|---|---|
| Unit | Domain rules: abstention, coverage, verification transitions, advisory validation, risk-band mapping |
| Integration | Input rules, feature engineering, model service contracts, database writes, notifications |
| End-to-end | Report → upload → inference → review → alert delivery → offline sync |
| Security | Authorisation boundaries, upload handling, data leakage, secrets management |
| Usability | Farmers completing tasks in realistic outdoor and network conditions |
| Model | Spatial/temporal holdouts, subgroup metrics, calibration, error analysis |

Rules:

- Link every requirement ID to at least one test.
- Include negative and failure cases: unsupported crop, blurry image, stale weather,
  offline, duplicate retry, unauthorised role, expired advisory.
- Test on a low-cost Android device and on a constrained network.
- Record expected result, actual result, evidence and defect reference.
- Test names describe behaviour, e.g. `test_blurry_image_returns_abstained_state`.

**Evidence required by change type** is listed in `./ai-workflow-rules.md` §9. The concrete
test-case catalogue lives in `./appendices.md` (Appendix F).

---

## 2. Pilot design and field validation (Chapter 46)

A controlled pilot is essential to learn whether the system helps real decisions. Start with
silent predictions before issuing operational alerts.

### 2.1 Site selection

Choose representative locations with extension partners and a feasible verification process.
Document the crop calendar and the epidemic window; plan the calendar around the disease,
not the funding cycle.

### 2.2 Silent phase

Generate predictions without farmer-facing alerts. Compare with verified field observations.
Log false alerts and missed events. Do not promote a model on training metrics.

### 2.3 Limited alert phase

Enable a small, approved set of alerts after thresholds and response workflows are reviewed.
Name the escalation owner for every alert type.

### 2.4 Evaluation

Track lead time, false alerts, missed events, review workload, farmer comprehension and
service reliability. Use a matched control area, a stepped-wedge design, or at minimum a
pre-registered lead-time measure. "Farmers who used it had less disease" is not evidence.

### 2.5 Decision

Expand only when evidence and operational capacity justify it. Negative results are
publishable and should be reported honestly.

**Implementation points**

- Document baseline conditions and the comparison method before launch.
- Do not claim yield impact without a suitable study design.
- Time the pilot to the epidemic season; a pilot that misses it produces no forecast
  evidence.

---

## 3. Deployment and infrastructure (Chapter 47)

Deployment is staged and reversible. Use separate development, staging and production
environments.

| Concern | Requirement |
|---|---|
| Environments | `dev` iterates fast; `staging` mirrors production and holds no real farmer data; `prod` has strict access, backups and monitoring |
| Release | Package services, run automated tests, apply migrations safely, use controlled rollout |
| Scaling | Scale image inference separately from API traffic when required |
| Backup | Database, object metadata, model artefacts and configuration |
| Recovery | Tested restore procedures with documented RTO/RPO |
| Infrastructure | Infrastructure-as-code where practical; rollback documented and tested |

Topology and service boundaries are in `./architecture-context.md` §10. Migrations are
forward-only, one logical change per revision, with a written rollback note.

---

## 4. Monitoring and model maintenance (Chapter 48)

Monitoring must detect software failures **and** model/data degradation. A model that worked
during development may behave differently after seasonal or geographic change.

| Area | Signals |
|---|---|
| Data | Missingness, freshness, duplicates, source changes, geography coverage |
| Model | Prediction distribution, abstention rate, verified performance, calibration drift |
| Product | Latency, error rates, upload backlog, sync success, notification delivery |
| Feedback | User complaints, expert corrections, field outcomes |

Retraining:

- Retrain only with governed, verified data.
- Repeat the frozen evaluation suite.
- Keep previous model versions for rollback.
- Never auto-promote a model based only on training metrics.
- Require manual registry approval before serving.

**Implementation points**

- Alert on data staleness before users see it.
- Track abstention and no-score rates as first-class operational metrics.
- Emit structured events without PII (see `./code-standards.md` §8).

---

## 5. Project team and responsibilities (Chapter 49)

Agronomy and field operations are as important as software engineering.

| Role | Owns |
|---|---|
| Product lead | Scope, user research, milestones, stakeholder communication, acceptance |
| Agronomist / pathologist | Target selection, taxonomy, labels, risk rules, advisory approval |
| Data engineer | Ingestion, storage, data quality, geospatial processing, lineage |
| ML engineer | Image and forecast modelling, evaluation, calibration, monitoring |
| Application engineers | Mobile, backend, portal, APIs, offline synchronisation |
| QA and field researcher | Test strategy, usability studies, field pilot, issue reporting |
| Field operations lead | Partner coordination, verification capacity, training, escalation |

**Staffing shape:** 7–9 people for the v1 scope. The first operational hire after
engineering is a field operations lead, not another ML engineer.

**Implementation points**

- Assign one accountable owner to each deliverable.
- Plan regular field feedback sessions throughout development.
- Track expert-review load as a staffing input, not an afterthought.

---

## 6. Success metrics and impact evaluation (Chapter 53)

Success is measured at multiple levels. Model accuracy is only one part.

| Level | Metrics |
|---|---|
| Technical | Image macro F1, per-class recall, calibration, abstention rate; forecast PR-AUC, Brier score, calibration; inference latency |
| Operational | Report-to-review time, review backlog, verified case rate, notification delivery, sync success |
| User | Task completion, comprehension of uncertainty wording, repeat use, alert usefulness, opt-out rate |
| Agricultural | Lead time, field-inspection prioritisation, outcome indicators where credible data exists |
| Equity | Performance and adoption by geography, device and user segment |

**Single most credible metric:** median lead time from first farmer report to verified expert
confirmation, compared with the existing advisory baseline. It is measurable, meaningful and
hard to fake. It must be pre-registered before the pilot.

Rules:

- Set a baseline before pilot deployment.
- Report limitations and sample sizes alongside claimed impact.
- Never report a single aggregate without the class/area breakdown.
- Use "not measured" when data cannot support a number.

---

## 7. Demonstration scenario (Chapter 54)

A demonstration shows the whole chain, end to end, using clearly labelled synthetic data.

1. A farmer selects a supported crop and area, photographs a leaf and submits a report.
2. The app flags blur and requests a retake; a clearer image receives a possible symptom
   match with medium confidence.
3. The local outlook separately shows moderate risk for a supported target over the next
   seven days, listing recent weather and crop stage as contributing factors.
4. The farmer receives scouting guidance and an option to request expert review.
5. The report appears as unverified in the expert queue.
6. An extension worker records a verification status; the dashboard updates the
   verified-report layer without conflating it with the forecast layer.

**Implementation points**

- Use synthetic demo data labelled `is_demo: true` everywhere it appears.
- Never present fabricated predictions as real local outbreak warnings.
- The seven-day window in this scenario is illustrative; D2 decides the shipped horizon.
- Rehearse the failure paths (blur, offline, stale outlook), not only the happy path.

---

## 8. Conclusion and future enhancements (Chapter 55)

The highest-value first step is not the most complex model; it is a dependable reporting and
verification workflow that produces trustworthy data.

**Future enhancements**

- Additional crops and target organisms after data readiness.
- On-device inference for selected models.
- Satellite or drone observations where validated.
- IoT sensors for local microclimate where economically justified.
- Advanced spatiotemporal forecasting after sufficient longitudinal data.
- Interoperability with institutional agricultural information systems.

**Final recommendation:** start with a narrow pilot, establish a high-quality dataset and
expert workflow, then expand only when each new crop and region has evidence to support
reliable service.

**Implementation points**

- Treat trust, usability and field outcomes as first-class success criteria.
- Re-read `./progress-tracker.md` before expanding scope.

---

## 9. Operational readiness checklist

- [ ] Test matrix links requirement, scenario, expected result and evidence.
- [ ] Silent-phase evidence reviewed before any operational alert.
- [ ] Alert response workflow staffed and escalation owners named.
- [ ] Backups and restore tested; RTO/RPO documented.
- [ ] Monitoring dashboards cover data, model and product metrics.
- [ ] Extension staff and admins trained.
- [ ] Expansion criteria written and approved.
- [ ] Launch-readiness checklist (Appendix H) signed off.

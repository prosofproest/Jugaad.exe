# Appendices

**Covers:** blueprint Appendices A–H — sample farmer alert, sample image assessment wording,
example forecast API response, database entity checklist, API and integration checklist,
example test cases, glossary, and the final launch-readiness checklist.
**Status:** reference templates. Every example is illustrative and marked as demo; no number,
name or payload here is real output.
**Last updated:** 2026-11-06

---

## Appendix A — Sample farmer-facing alert

> **MODERATE LOCAL RISK.** Conditions in the selected area may be favourable for
> [supported crop issue] during [forecast period]. This is an early warning, not
> confirmation that your field is infected.

**Why this alert was issued**

> Recent weather conditions and the current crop stage match factors associated with
> increased risk. The area currently has [coverage status] data coverage. The most recent
> input was updated at [timestamp].

**What to do now**

> Inspect a sample of plants across the field, record whether symptoms are increasing,
> follow the locally approved prevention advisory and contact an extension worker if
> matching symptoms are observed.

**Required metadata:** forecast issue time, valid-from and valid-to time, crop, target,
administrative area, model version, coverage status and advisory version.

**Implementation points**

- Never recommend pesticide application solely because a forecast alert was issued.
- Every alert states "early warning, not confirmation".
- Low coverage blocks the alert regardless of band.

---

## Appendix B — Sample image assessment wording

> **POSSIBLE SYMPTOM MATCH.** The submitted image appears most similar to [condition A].
> The assessment confidence is [validated band] and the photo quality is [status]. This is
> an automated visual assessment, not a confirmed diagnosis.

**Next step**

> Inspect additional plants and compare symptoms with the locally approved advisory. If the
> image is unclear, the crop is unsupported or symptoms do not match, request expert review.

**Separate forecast context**

> An area-level forecast may provide additional context but does not confirm the condition
> on the photographed plant.

**Result metadata:** image ID, model version, generated timestamp, supported class set,
quality flags, abstention status and score calibration status.

**Implementation points**

- Use plain language and translate with local agricultural experts.
- Abstained state: "No assessment yet — this photo is too blurry … Retake in daylight."
  Never show a candidate list when abstained.
- The card title is always "Photo assessment", never "Diagnosis".

---

## Appendix C — Example forecast API response

The following is a schema illustration, not a real forecast. It shows the fields needed to
make a forecast interpretable and auditable.

```json
{
  "forecast_id": "fcst_demo_001",
  "crop": "example_crop",
  "target": "example_target",
  "geography": {"level": "administrative_block", "code": "DEMO_BLOCK"},
  "issue_time": "2026-11-06T06:00:00Z",
  "valid_from": "2026-11-06T06:00:00Z",
  "valid_to": "2026-11-13T06:00:00Z",
  "risk_band": "moderate",
  "probability": null,
  "confidence": "medium",
  "data_coverage": "good",
  "drivers": ["recent_rainfall", "crop_stage"],
  "model_version": "forecast-demo-0.1",
  "is_demo": true
}
```

**Interpretation:** `probability` is `null` because a calibrated probability has not been
approved in this illustrative payload. A production response includes a probability only
when validation supports it.

**Implementation points**

- Keep example data visibly marked as demo or synthetic.
- The API response never merges photo assessment and area outlook into one object.

---

## Appendix D — Database entity checklist

A practical starting point for the relational model. The final schema is reviewed against
the chosen workflows and privacy requirements in `../feature-specs/05-data-layer.md`.

**Core entities**

- User and role.
- Growing area and approximate geometry.
- Crop cycle and crop-stage history.
- Observation and image asset.
- Image quality result and image prediction.
- Forecast and feature snapshot.
- Advisory, version and approval history.
- Expert review, evidence and verification projection.
- Alert, delivery and feedback.
- Audit event and consent record.
- Model registry and export job.

**Integrity requirements:** stable identifiers, foreign keys, status constraints, source
timestamps, model versions and append-only prediction history.

**Implementation points**

- Use PostGIS only where spatial queries are required.
- Restrict access to precise location fields.
- Suppress small counts in a view or function, not in the UI.

---

## Appendix E — API and integration checklist

Before connecting the mobile app and AI services, agree the contract and error behaviour.

**API checklist**

- Versioned routes and documented schemas.
- Authentication and role-based access.
- Idempotency for report creation and uploads.
- Pagination and filtering for case queues.
- Structured error codes and retry guidance.
- Request size and file validation.
- Audit trail for expert changes.
- No raw model scores, feature vectors or storage keys to farmer clients.

**Integration checklist**

- Weather source licence and freshness.
- Boundary dataset version and area codes.
- Map provider terms and offline behaviour.
- Notification opt-in and delivery receipts.
- Approved advisory source and content review.

**Implementation points**

- Test external provider outage and delayed responses.
- Every external feature row stores `source_timestamp` and `fetched_at`.

---

## Appendix F — Example test cases

These examples convert into formal test cases in a quality-management tool.

**Functional**

- Submit a supported crop image with a valid network.
- Submit a blurry image and confirm the app requests a retake; no candidates shown.
- Submit an unsupported crop and confirm no unsupported assessment is forced.
- Save a report offline and synchronise after reconnecting.
- Retry an upload and confirm no duplicate observation is created.
- Confirm only authorised experts can change review status.
- Confirm an extension worker cannot set `confirmed`; a pathologist can.
- Confirm the result screen renders two separate cards with distinct titles and timestamps.

**Forecast**

- Return a current forecast with issue and expiry times.
- Return `insufficient_data` when the weather feed is stale.
- Return `insufficient_data` when coverage is below threshold.
- Confirm map layers distinguish verified reports, unverified reports and predictions.
- Confirm an expired cached forecast is marked stale, including offline.
- Confirm an unverified report is excluded from forecast features.
- Confirm `probability` is `null` unless calibration is approved.

**Security**

- Attempt unauthorised access to another farmer's report.
- Upload an invalid file type.
- Attempt access to a private image URL after expiry.
- Confirm sensitive exports are role-restricted and audited.
- Confirm admin record views require a reason and write an audit event.

**Advisory**

- Validator rejects product names, doses, mixtures, application intervals, pre-harvest
  intervals, legal-use claims and guarantees.
- Advisory cannot be published without a second approver.
- Expired advisory is not returned by the API.
- Missing advisory returns a fallback plus escalation, never generated text.

**Implementation points**

- Record expected result, actual result, evidence and defect reference.
- Include at least one negative case for every positive case.

---

## Appendix G — Glossary

| Term | Definition |
|---|---|
| Photo assessment | Automated triage of visible symptoms in an individual image |
| Area outlook | Estimated future risk for target × crop × geography × horizon |
| Calibration | Agreement between predicted probabilities and observed frequencies |
| Abstention | A model decision not to answer when evidence is insufficient |
| Data leakage | Use of information during training that is unavailable at prediction time |
| Temporal holdout | Evaluation on a later period not used for training |
| Surveillance intensity | Amount of reporting or inspection activity in an area |
| Coverage | Completeness, freshness and representativeness of inputs |
| Model drift | Change in input patterns or performance over time |
| Verification | Human decision on a report: confirmed, probable, rejected, duplicate, needs visit, unresolved |
| Target | A supported pest/disease condition on the supported crop list |
| Supported | Explicitly in the approved crop/target/geography list for the current release |
| Stale | Past its validity window; must be visually distinct from fresh data |
| Demo / synthetic | Illustrative data that must be labelled `is_demo` in data, API and UI |

The canonical product vocabulary is in `./AGENTS.md` §10; this table mirrors it for
readers coming from the blueprint.

---

## Appendix H — Final launch-readiness checklist

The project is not launched as an operational early-warning service until these gates are
reviewed and signed off.

**Agronomy and data**

- [ ] Crop and target scope approved by local experts.
- [ ] Label handbook and verification workflow active.
- [ ] Data permissions and provenance documented.
- [ ] Weather and boundary data freshness monitored.

**AI and product**

- [ ] Image and forecast models evaluated separately.
- [ ] Calibration and abstention behaviour tested.
- [ ] Risk map distinguishes reports, predictions and coverage.
- [ ] Advisories approved and versioned.
- [ ] Offline queue and stale-data handling tested.

**Operations and governance**

- [ ] Consent, privacy and retention procedures active.
- [ ] Security review completed.
- [ ] Alert thresholds and escalation owners approved.
- [ ] Monitoring, rollback and incident response ready.
- [ ] Pilot findings reviewed and documented.

**Implementation points**

- If a gate is not met, keep the affected feature in a non-operational or silent pilot mode.

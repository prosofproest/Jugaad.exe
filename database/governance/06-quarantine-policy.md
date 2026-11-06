# Quarantine policy

**Status:** Draft.
**Owner:** Data engineer + data owner (TBD)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/data-foundation.md` §2.4, §5;
`final/docs-context/phase-plan.md` §4.7.

> **Rule:** a suspicious record is never silently dropped. It is quarantined, assigned,
> investigated and resolved with an audit trail. Quarantine is not deletion.

---

## 1. Purpose

Define what happens when an ingested record fails a quality, provenance, permission or
privacy check, so that:

- the original is preserved;
- the failure is visible;
- no quarantined record enters training, evaluation, forecasting or advisory content;
- the resolution is owned and auditable;
- deletion is a deliberate, approved act, not a side effect of cleaning.

---

## 2. Scope

Applies to:

- images and their metadata;
- tabular observation and crop-context records;
- weather and boundary data;
- historical occurrence records;
- advisory content;
- model artefacts and dataset versions.

---

## 3. What counts as suspicious

| Category | Examples |
|---|---|
| File integrity | Corrupt file, unsupported type, zero bytes, truncated upload |
| Image quality | Blur beyond threshold, underexposed/overexposed, wrong orientation, no plant visible |
| Duplicate | Exact content hash match; perceptual hash match; duplicate report |
| Metadata | Missing crop, missing area, invalid date, impossible growth stage, unit mismatch |
| Geography | Unmatched boundary code, missing boundary version, area outside the pilot |
| Provenance | No source, no permission record, no reviewer identity, missing event date |
| Consent | Required consent absent or outdated |
| Label | Conflicting labels, unsupported class, forced positive on an ambiguous image |
| Domain | Input outside the model's validated crop/target/device domain |
| Weather | Impossible value, stale provider record, gap, grid mismatch |
| Privacy | Image contains a face, document, precise location or other personal data without the required consent |
| Permission | Dataset licence expired or use outside the permitted scope |
| Demo leakage | Demo/synthetic record mixed into an operational dataset without `is_demo` |

---

## 4. Quarantine states

```
ingested
  → validated            (normal path; leaves the quarantine workflow)
  → quarantined          (failed a check)
      → under_review
          → released     (accepted with documented justification)
          → rejected     (not usable; retained or deleted per retention)
          → deleted      (approved deletion; legal hold checked)
          → escalated    (needs data owner, agronomist, legal or privacy review)
```

Rules:

- `quarantined` is not `deleted`.
- A record can leave quarantine only through a recorded resolution.
- `released` requires a reason and an approver; it does not erase the original failure.
- `rejected` records are excluded from all model and forecast datasets.
- `deleted` requires retention approval and a legal-hold check.
- A record can move back to `quarantined` if new evidence appears.

---

## 5. Required record fields

Proposed schema for the quarantine queue. Reconcile with
`final/feature-specs/05-data-layer.md` before implementation; that spec currently has no
quarantine table.

| Field | Type | Requirement |
|---|---|---|
| `id` | uuid | Primary key |
| `dataset_id` | text | Links to the dataset register |
| `dataset_version` | text | Version being ingested |
| `batch_id` | text | Ingestion batch |
| `record_type` | text | image, observation, weather, boundary, label, advisory, model |
| `record_id` | text | Source record identifier |
| `source_ref` | text | Source location or pointer |
| `reason_code` | text | From the controlled list |
| `reason_detail` | text | Human-readable explanation; no PII |
| `severity` | text | `low`, `medium`, `high`, `blocking` |
| `detected_at` | timestamptz | When detected |
| `detected_by` | text | Rule/job or person |
| `status` | text | Quarantine state |
| `assigned_to` | uuid | Accountable resolver |
| `resolution` | text | Outcome and justification |
| `resolved_at` | timestamptz | When resolved |
| `resolved_by` | uuid | Approver |
| `original_preserved` | boolean | Must be true until approved deletion |
| `evidence_ref` | text | Link to inspection or evidence |
| `is_demo` | boolean | Demo marker |
| `notes` | text | No PII |

A separate immutable `quarantine_events` table should record every state change.

---

## 6. Reason codes

```
file_corrupt
unsupported_type
zero_bytes
dimensions_invalid
duplicate_hash
duplicate_perceptual
blur
exposure
orientation
no_plant
metadata_missing
unit_invalid
date_impossible
crop_unknown
stage_impossible
geo_unmatched
boundary_missing
consent_missing
permission_missing
provenance_missing
label_conflict
unsupported_class
out_of_domain
weather_anomaly
weather_stale
boundary_mismatch
pii_detected
demo_leakage
```

New codes require a documented reason; do not reuse a code for a different failure.

---

## 7. Workflow

1. **Detect.** Automated checks or a human reviewer flag the record.
2. **Quarantine.** Write the quarantine row; preserve the original; exclude it from
   downstream datasets.
3. **Notify.** Alert the assigned data owner and, for privacy or permission issues, the
   legal/privacy owner.
4. **Triage.** Assign severity and owner; set a resolution target.
5. **Investigate.** Inspect the original, source, metadata and provenance.
6. **Resolve.** Choose `released`, `rejected`, `deleted` or `escalated`.
7. **Record.** Write the resolution, evidence and approver; append an event.
8. **Re-ingest if applicable.** A released record may re-enter the pipeline only with a
   new validation result.
9. **Report.** Update the quality dashboard and the dataset register.

### Resolution targets

| Severity | Target |
|---|---|
| `blocking` | Same day; stops the batch |
| `high` | 2 working days |
| `medium` | 5 working days |
| `low` | 15 working days |

Targets are operational defaults; the programme may tighten them.

---

## 8. Batch handling

- A batch with a `blocking` failure does not proceed to model-ready status.
- Non-blocking failures may be quarantined while the rest of the batch proceeds, provided
  the batch report records the excluded count.
- The batch is versioned; a re-run creates a new version, never mutates the old one.
- The data-quality report states: total records, passed, quarantined, rejected, deleted,
  and reasons.

---

## 9. What must never happen

- A record is deleted because a validator failed.
- A quarantined record is used for training, evaluation or forecasting.
- A duplicate is merged without a review decision.
- A label is overwritten without an audit record.
- A privacy failure is resolved by editing the original and discarding the evidence.
- A failing batch is silently marked complete.
- A `released` record loses its original failure history.
- Real personal data is copied into the quarantine notes.

---

## 10. Roles

| Role | Responsibility |
|---|---|
| Data engineer | Owns the queue, rules, metrics and tooling |
| Data owner | Resolves dataset and permission issues |
| Agronomist / pathologist | Resolves label and taxonomy conflicts |
| Legal / privacy | Resolves consent, PII and permission issues |
| Field operations lead | Resolves capture and provenance issues |
| QA | Audits resolutions and samples released records |

---

## 11. Metrics

- Quarantine rate by dataset, batch and reason.
- Open backlog by severity and age.
- Resolution time.
- Release rate after review.
- Repeat failure rate for the same source.
- Deletion count and approvals.
- Privacy/permission incidents.

---

## 12. Acceptance criteria

- [ ] A corrupt image is quarantined, not deleted, and the original remains retrievable.
- [ ] A duplicate is quarantined and linked; no silent merge.
- [ ] A missing-consent record is excluded from all downstream datasets.
- [ ] A permission-expired dataset is blocked from ingestion.
- [ ] A quarantined record is excluded from training and forecasting (tested).
- [ ] Every resolution has an owner, reason, timestamp and audit event.
- [ ] A `blocking` failure prevents batch release.
- [ ] A privacy failure escalates to the privacy owner.
- [ ] Deletion from quarantine requires approval and a legal-hold check.
- [ ] The quality report reconciles total, passed, quarantined, rejected and deleted
      counts.

---

## 13. Open questions

1. Where will the quarantine queue live — database table, object-store manifest, or both?
2. What is the retention period for rejected records?
3. Who approves deletion of a rejected record?
4. What is the SLA for privacy-related quarantine?
5. Are quarantine records included in the data dictionary and dataset register?
6. Should the quarantine queue be visible to partners?

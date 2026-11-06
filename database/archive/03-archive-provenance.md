# Archive provenance and chain of custody

**Version:** `v1.0-draft`
**Status:** Draft — **no archive record, source link or reviewer identity exists yet.**
**Owner:** Data engineer (custody and manifests); Pathologist (label provenance);
Legal/privacy (personal-data handling)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/phase-plan.md` §4.3;
`final/docs-context/data-foundation.md` §2.4, §8;
`final/feature-specs/05-data-layer.md`;
`final/docs-context/AGENTS.md` R6, R7, R9;
`final/TRD.md` §6.9.

> **Rule:** if the source, original label, reviewer and permission cannot be reconstructed
> from the record and its manifest, the record is not usable — and it is quarantined, not
> discarded.

---

## 1. Purpose

Archive data arrives from outside the project. Its value depends entirely on being able to
answer, for every record:

1. Where did it come from, and can that be checked later?
2. What did the archive call it, in the archive's own words?
3. Who reviewed or corrected it, and under what authority?
4. What did the project change, when, and against which version?
5. What permission allowed this use?
6. Can the exact bytes be verified as the ones received?

This document defines the fields, files and custody rules that make those answers possible.

---

## 2. Chain of custody

```
archive institution
  → access request + signed permission record
  → delivery (download, disk, API) with a delivery note
  → intake manifest (batch_id, checksums, counts)
  → immutable originals in the archive prefix
  → provenance sidecar per record
  → reconciliation mapping (02-label-reconciliation.md)
  → quarantine for anything unresolved
  → versioned archive batch
  → dataset register entry (ARC-###)
```

At every hop the batch has an owner, a timestamp and a hash. A hop without a record breaks
the chain, and the affected records are `provenance_missing`.

---

## 3. Required provenance per record

| Field | Type | Requirement | Missing meaning |
|---|---|---|---|
| `archive_source_id` | text | `ARC-###` from the dataset register | Record not attributable; quarantine |
| `archive_record_id` | text | The archive's own stable identifier | Cannot re-check the source; quarantine |
| `source_link` | text | URL, accession reference or contact route | `provenance_missing` |
| `source_link_checked_at` | timestamptz | When the link was last verified | Link status unknown |
| `source_link_status` | text | `live`, `dead`, `restricted`, `not_public` | Treated as unverified |
| `original_label` | text | Verbatim archive label, original language | `original_label_missing` |
| `original_label_code` | text | Archive's own class code, if any | No code available |
| `original_language` | text | ISO 639 code, or `unknown` | Translation risk; flag |
| `label_scheme` | text | Archive's labelling scheme name | Scheme unknown; mapping blocked |
| `label_scheme_version` | text | Version or date of the scheme | Version unverified |
| `archive_reviewer_ref` | text | Archive reviewer/assessor reference, if given | Reviewer unknown |
| `archive_review_date` | date | When the archive assessed it | Date unknown |
| `original_metadata` | jsonb | The archive's metadata as received, unedited | Metadata not preserved |
| `mapped_label` | text | Project class after reconciliation | Not mapped |
| `taxonomy_version` | text | Taxonomy used for the mapping | Mapping blocked |
| `mapped_by` / `reviewed_by` | uuid | Project mapper and pathologist approver | Mapping not approved |
| `mapped_at` / `reviewed_at` | timestamptz | UTC | Mapping undated |
| `permission_id` | text | Linked permission record | `permission_missing` |
| `permitted_use` | text | Exact use allowed | Not usable |
| `retention_rule` | text | Approved period/trigger | Cannot be cleared |
| `content_hash` | text | SHA-256 of the original bytes | Integrity unverified |
| `manifest_id` | text | Batch manifest that delivered it | Custody broken |
| `received_at` | timestamptz | UTC | Receipt undated |
| `provenance_status` | text | `complete`, `partial`, `missing`, `disputed` | Treat as `missing` |
| `provenance_notes` | text | No PII; states what is missing and why | No explanation |

`provenance_status = complete` requires: source id, source link or accession, original
label, label scheme, a content hash and a permission id. Everything else is `partial` or
`missing` and is quarantined.

---

## 4. Reviewer identity handling

Reviewer identity is needed for auditability and is also personal data.

| Rule | Requirement |
|---|---|
| Store an account reference | Store `reviewed_by` as an internal user/account ID, not a name, email or phone number |
| Do not copy archive PII | If the archive supplies a reviewer's name or contact details, record the fact that a reviewer existed; do not copy the details into general metadata |
| Access | Reviewer identity is visible only to authorised review/admin roles, never in farmer-facing output, exports or dashboards |
| Retention | Follow `../governance/05-retention-and-deletion.md`; reviewer references are retained as audit evidence, minimised where possible |
| External reviewers | If an external pathologist reviews, their identity is covered by a contract or agreement before any record is stored |
| No invented reviewer | An unnamed reviewer is `unknown`; never fill in a plausible name or role |
| Separation of duties | The person who proposes a mapping is not the sole approver; approval requires the pathologist role |

---

## 5. Batch manifest

Every archive batch has a manifest file stored with the batch, not inside the database only.
It is the custody record.

| Manifest field | Requirement |
|---|---|
| `batch_id` | Stable, unique; includes `ARC-###` and a date |
| `archive_source_id` | `ARC-###` |
| `batch_version` | Monotonic |
| `received_at` | UTC |
| `delivery_method` | Download, disk, API or other |
| `delivery_note_ref` | Where the delivery note is stored |
| `permission_id` | Signed permission record |
| `record_count` / `image_count` | Declared by the archive |
| `received_count` / `verified_count` | Counted at intake |
| `checksum_algorithm` | `sha256` |
| `checksums_file` | Path to the per-record hash list |
| `metadata_schema` | Archive metadata schema and version |
| `label_scheme` / `label_scheme_version` | As supplied |
| `taxonomy_version` | Project taxonomy used for mapping |
| `mapping_report_ref` | `02-label-reconciliation.md` output |
| `quarantine_report_ref` | Quarantine counts and reasons |
| `accepted` / `restricted` / `rejected` | Counts |
| `manifest_hash` | SHA-256 of the manifest itself |
| `created_by` / `approved_by` | Data engineer / data owner |
| `created_at` | UTC |

**Counts must reconcile:** received = accepted + restricted + rejected + quarantined
(+ duplicates explicitly linked). An unreconciled manifest blocks the batch.

---

## 6. Batch evidence package

For every accepted batch, keep a self-contained evidence package:

```
archive/<arc_id>/<batch_version>/
  manifest.json
  checksums.sha256
  permission-record.(pdf|md)
  delivery-note.(pdf|md)
  metadata-schema.(json|md)
  mapping-report.(csv|md)
  quarantine-report.(csv|md)
  provenance/
    <archive_record_id>.json      # sidecar; original metadata + source link
  originals/
    <archive_record_id>/original.<ext>
```

Rules:

- `originals/` is read-only; no edit, crop or re-save.
- The sidecar preserves the original label and source link even if the source later dies.
- The package is versioned; a new delivery creates a new `batch_version`.
- The package is access-controlled and never served to farmers.
- No PII is added to the package; archive-supplied PII is quarantined and handled separately.

---

## 7. Integrity and deduplication

- Every original file has a SHA-256 recorded at receipt and re-verified after transfer.
- A file whose hash does not match the manifest is quarantined (`file_corrupt` or
  `provenance_missing`).
- Exact duplicates are linked by hash, not merged.
- Near-duplicates use a perceptual hash and are quarantined (`duplicate_perceptual`) for
  review.
- Archive records are also checked **against field data**; a match is quarantined and
  linked, never silently dropped or allowed to cross into the field set.
- A restored backup is re-verified against the manifest before use.

---

## 8. Provenance failure handling

| Condition | Reason code | Action |
|---|---|---|
| No source id or link | `provenance_missing` | Quarantine; request from institution |
| No original label | `original_label_missing` | Quarantine; do not infer a label |
| Label scheme unknown | `label_conflict` / `metadata_missing` | Quarantine; pathologist review |
| No permission record | `permission_missing` | Block batch |
| Use outside permitted scope | `permission_scope` | Quarantine and legal review |
| Reviewer unknown | `provenance_missing` | Record `unknown`; mapping needs pathologist approval |
| Checksum mismatch | `file_corrupt` | Quarantine; re-request the file |
| Source link dead | `provenance_missing` | Keep sidecar; mark link `dead`; re-verify |
| Metadata contradicts label | `label_conflict` | Quarantine; pathologist review |

A provenance failure never results in deletion of the original.

---

## 9. Link rot and long-term traceability

- Store the source link **and** a retrieved snapshot or accession reference where the
  permission allows it.
- Record when the link was last checked and its status.
- Do not replace a dead link with a guessed one.
- If the institution withdraws or moves the collection, record it and follow the
  retention/deletion instruction in the permission record.
- The mapping report and manifest stay with the batch for its full retention period.

---

## 10. Privacy in provenance records

- No farmer names, phone numbers, faces or precise coordinates in manifests, mapping
  reports or quarantine notes.
- If the archive includes such data, it is quarantined and handled under the privacy
  procedure; the manifest records only that personal data was present and how it was
  handled.
- Source links that embed a token or personal identifier are stored access-controlled and
  are never pasted into reports.
- Reviewer identity is an account reference, minimised and role-gated.

---

## 11. Relationship to the schema

`final/feature-specs/05-data-layer.md` has **no archive tables** today. This document
proposes the fields that must exist before an archive is ingested. Until those tables (or a
documented JSONB sidecar with constraints) are added by a migration, archive ingest cannot
satisfy this control set.

Proposed tables, to be reconciled with the data layer spec and the data dictionary:

- `archive_sources` — `ARC-###`, institution reference, permission id, status;
- `archive_batches` — manifest fields and counts;
- `archive_records` — source/record id, source link, original label and scheme, hashes;
- `archive_label_mappings` — the mapping table in `02-label-reconciliation.md`;
- `archive_provenance_events` — append-only custody and review events.

---

## 12. What must never happen

- Ingesting a record with no source and no way to trace it.
- Editing or re-saving an archive original.
- Overwriting the original label or the archive metadata.
- Copying archive PII into a manifest, report or note.
- Filling a missing reviewer, date or source link with a plausible value.
- Deleting a record because provenance is incomplete.
- Merging duplicates without a review decision.
- Treating a dead source link as permission to re-host the image.
- Letting archive records cross into the field dataset or split manifest.

---

## 13. Acceptance criteria

- [ ] Every accepted record has a source id, source link or accession, original label and
      content hash, or a recorded reason why not.
- [ ] Every batch has a manifest, checksums file and reconciling counts.
- [ ] Every original is read-only and hash-verified.
- [ ] Every mapping names a taxonomy version and a pathologist reviewer.
- [ ] Reviewer identity is stored as an account reference and role-gated.
- [ ] Provenance failures are quarantined with a reason code, not deleted.
- [ ] Archive records are checked against field data for duplicates.
- [ ] The evidence package is complete and versioned.
- [ ] Archive records never enter a field dataset version, split manifest or frozen test
      set.
- [ ] The dataset register shows the batch, version and counts separately from field data.

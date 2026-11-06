# Archive acquisition

**Version:** `v1.0-draft`
**Status:** Draft — **no archive access requested, no archive data in hand, no partner named.**
**Owner:** Data engineer (TBD), with Pathologist (taxonomy) and Legal/privacy (TBD)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/phase-plan.md` §4.3;
`final/docs-context/data-foundation.md` §2, §3.5, §8;
`final/update.md` D2 (archive path);
`final/feature-specs/05-data-layer.md`;
`final/docs-context/AGENTS.md` R4, R6, R9.

> **Boundary:** an AI agent cannot request, accept, license or ingest an archive. This
> document defines the gate, the intake process and the separation rules. Only an
> authorised human may sign the permission record and mark an archive `cleared`.

---

## 1. Why archives

Plant-clinic and university pathology archives are often the highest-value source available
before a pilot produces field data: they are already labelled by experts, cover historical
seasons and may include conditions that are rare in a single collection window.

They are also the easiest source to misuse. An archive is not fresh field data. It was
captured on unknown devices, at unknown distances, under a different labelling scheme, in a
different era, and possibly for a different purpose. Treating it as field data creates
domain shift and leaks archive conditions into the field test set.

**Rule:** archives may be used for training and pretraining where permission allows. They
are **never** the field validation set and **never** part of the frozen field test set.

---

## 2. Definitions

| Term | Definition |
|---|---|
| **Archive source** | An institution and collection offered under a permission record (for example a plant-clinic network or a university pathology department). |
| **Archive record** | One archived case or specimen record, with its own identifier, image(s), original label and metadata. |
| **Original label** | The label exactly as recorded by the archive, in its original language and scheme. Never overwritten. |
| **Mapped label** | The project taxonomy class assigned by reconciliation (`02-label-reconciliation.md`). A separate field. |
| **Archive batch** | One versioned ingest from one archive source, with a manifest and checksums. |
| **Field data** | Data captured by the project's own collectors or farmers under the capture protocol and consent. |

---

## 3. Candidate archive sub-register

This is a sub-register of `../governance/01-dataset-register.md`. IDs are stable and never
reused. No institution is named because none has been approached.

| ID | Source type | Institution | Status | Permission record | Permitted use | Owner | Retention | Quality check |
|---|---|---|---|---|---|---|---|---|
| `ARC-001` | Plant-clinic archive (Plantwise-style) | `TBD` | `candidate` | None — not executed | None yet | TBD | TBD | Provenance + label reconciliation + PII |
| `ARC-002` | University pathology department archive | `TBD` | `candidate` | None — not executed | None yet | TBD | TBD | Provenance + label reconciliation + PII |

**Both rows are `candidate`.** No access request exists, no sample has been seen, and no
permission has been granted.

---

## 4. Permission gate

An archive may be ingested only when a signed permission record covers **all** of the
following. If any item is missing, the archive is `not_acquired`.

| Item | Requirement |
|---|---|
| Parties | Named institution and authorised signatory |
| Material | Dataset description, record count, image count, date range, format |
| Permitted use | Explicit permission for ML training, evaluation and benchmarking, or an explicit narrower scope |
| Prohibited use | Stated exclusions (for example no commercial use, no redistribution) |
| Derivatives | Whether mapped labels, features, crops and trained models may be created and retained |
| Redistribution | Whether images, derivatives or models may be published or shared |
| Personal data | Whether the archive contains people, faces, names, contact details or farm identifiers, and the lawful basis supplied by the institution |
| Location | Whether precise location is present, and whether it may be used |
| Attribution | Citation format and any required acknowledgement |
| Retention | Period for originals, derivatives and model artefacts |
| Deletion | Return or destruction obligations on termination |
| Security | Storage location, access control and breach notification |
| Audit | Whether the institution may inspect use |

A public download link, a personal email, a verbal assurance or "it is on the website" is
**not** a permission record. Scraping an archive is prohibited.

---

## 5. Eligibility criteria

An archive is eligible for intake only when all of these are true:

- [ ] A signed permission record exists and matches the actual material.
- [ ] The institution can supply a record-level identifier and a source link.
- [ ] The original label, label scheme and reviewer information are available, or their
      absence is documented.
- [ ] The images are retrievable at usable resolution, not only thumbnails.
- [ ] The archive's crop and condition set overlaps the project taxonomy, or the unmappable
      portion can be isolated.
- [ ] Personal data has been assessed and a handling rule exists.
- [ ] A sample has passed file-integrity and image-quality checks.
- [ ] The archive can be versioned and checksummed as a batch.

An archive that fails a criterion is recorded as `rejected` or `restricted` with the reason,
not silently skipped.

---

## 6. Intake workflow

```
identify source
  → request access (human signatory)
  → legal/privacy review
  → receive sample + metadata schema
  → file-integrity and duplicate check
  → image-quality check
  → provenance audit
  → label reconciliation (02-label-reconciliation.md)
  → quarantine unmappable / failed / privacy records
  → register batch and version
  → accept, restrict or reject
  → record in dataset register
```

### 6.1 Step detail

1. **Identify.** Record the institution, collection, contact and intended use in `ARC-###`.
2. **Request.** A human requests access; the request and response are stored with the
   permission record.
3. **Review.** Legal/privacy reviews personal data, location, redistribution and retention.
4. **Sample.** Ingest 20–50 records (or `TBD` if the archive is smaller) before the full
   batch. Do not build a pipeline against an unseen schema.
5. **Integrity.** Verify file type, size, checksum and duplicates. Corrupt records go to
   quarantine, not to the bin.
6. **Quality.** Run the same image-quality gate as field images where the inputs allow it.
   Archive images may be scans or low-resolution; record `not_comparable` rather than forcing
   a pass.
7. **Provenance.** Confirm every record has a source link, an original label and a reviewer
   reference, or record exactly what is missing (`03-archive-provenance.md`).
8. **Reconcile.** Map labels to the project taxonomy and flag unmappable records
   (`02-label-reconciliation.md`).
9. **Quarantine.** Any failed, unmappable, privacy-affected or provenance-missing record is
   quarantined under `../governance/06-quarantine-policy.md`.
10. **Register.** Record the batch, version, checksums, counts and split role in the dataset
    register.
11. **Decide.** Mark `cleared`, `restricted` or `rejected`. A partial acceptance is normal;
    record the exclusions.

---

## 7. Separation from field data

This is a hard rule, not a preference.

| Rule | Requirement |
|---|---|
| Separate register rows | Archive sources use `ARC-###` under `DS-002`; field sources use `DS-001`/`DS-005` |
| Separate dataset versions | An archive batch and a field batch never share a `dataset_version` |
| Separate object prefixes | Archive originals live under an `archive/` prefix, not `observations/` |
| Separate split manifests | Archive records never enter the field split manifest |
| No field test set | Archive records are never part of the frozen field test set |
| No silent mixing | A model-ready dataset that combines field and archive data must be a named, versioned union with per-source counts |
| Reported separately | Metrics on archive-only data are labelled `archive`; they are not field evidence |
| Register visibility | The register shows archive rows separately and never folds them into a field total |

**Why:** archive and field data differ in device, era, framing, label scheme and population.
Mixing them without a recorded union hides domain shift and inflates apparent field
performance.

---

## 8. Storage

- Archive originals are stored read-only in a separate private prefix, for example
  `archive/<arc_id>/<batch_version>/<record_id>/original.<ext>`.
- The original file is never edited. A derivative is a separate object with a pipeline
  version.
- Every object has a SHA-256 checksum in the batch manifest.
- A metadata sidecar preserves the original label, scheme, language and source link even if
  the source URL later dies.
- Access is role-restricted; archive data is not shown in farmer-facing surfaces.
- Retention and deletion follow the permission record and
  `../governance/05-retention-and-deletion.md`.
- Copyright and licence terms are recorded per source; no re-hosting beyond the permission.

---

## 9. Quality checks

| Check | Failure action |
|---|---|
| Permission record present and covers the material | Block the batch |
| File integrity and checksum | Quarantine record |
| Duplicate within archive or against field data | Quarantine; link, do not merge |
| Image readable at usable resolution | Quarantine or mark `not_comparable` |
| Source link and accession ID present | Quarantine `provenance_missing` |
| Original label present | Quarantine `original_label_missing` |
| Original label mapped or explicitly unmappable | Quarantine `label_unmappable` |
| Taxonomy version recorded | Block the mapping |
| Personal data / face detected | Quarantine `pii_detected`; privacy review |
| Crop outside the supported list | Quarantine `crop_unknown` |
| Record outside the permitted date or geography scope | Quarantine `permission_scope` |

The batch report states: received, accepted, quarantined, unmappable, rejected and excluded,
with reasons. Counts must reconcile.

---

## 10. What must never happen

- Ingesting an archive without a signed permission record.
- Scraping a website because the images are visible.
- Treating an archive as field validation data.
- Folding archive and field counts into one unlabelled total.
- Overwriting an original label with the mapped label.
- Inventing a reviewer, a date or a label scheme.
- Deleting a record because its label cannot be mapped.
- Copying personal data into a batch report or quarantine note.
- Re-hosting copyrighted archive images beyond the permission.

---

## 11. Acceptance criteria

- [ ] Every archive source has an `ARC-###` row and a permission record before ingest.
- [ ] No archive record enters a field dataset version or split manifest.
- [ ] Archive data is excluded from the frozen field test set.
- [ ] Every record has a source link, original label and provenance status, or a recorded
      reason why not.
- [ ] Unmappable records are quarantined, not deleted or forced into a class.
- [ ] Archive and field counts are reported separately.
- [ ] Each batch has a manifest, checksum and reconciliation report.
- [ ] Personal data in archive images is quarantined and reviewed.
- [ ] A rejected archive is recorded with a reason.
- [ ] The register shows archive rows separately from field rows.

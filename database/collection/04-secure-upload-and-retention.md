# Secure upload, backup and image retention

**Version:** `v1.0-draft`
**Status:** Draft — no storage provisioned.
**Owner:** Data engineer (TBD) + Legal/privacy (TBD)
**Last updated:** 2026-11-06
**Authorities:** `final/feature-specs/05-data-layer.md` §8, §11, §12;
`final/TRD.md` §6; `../governance/05-retention-and-deletion.md`;
`../governance/06-quarantine-policy.md`.

> **Rule:** the **original image is the legal record**. It is stored once, immutably, in a
> private bucket. Every processed version is a derivative that can be regenerated and can
> never overwrite or replace the original.
>
> **Boundary:** retention periods are `TBD` pending legal/programme decision (D4). This
> document specifies the mechanism, not the number of years.

---

## 1. Storage layers

| Layer | Location | Lifetime | Contents | Authority |
|---|---|---|---|---|
| Capture buffer | Device, app-private storage | Until upload confirmed | Originals + metadata, encrypted if the platform supports it | Device |
| Upload staging | Private bucket, temporary prefix | Short TTL; deleted after verification | In-flight multipart parts | Server |
| **Original store** | Private bucket, `original` object | Immutable; retention `TBD` | The untouched file exactly as captured | Server |
| Derivative store | Private bucket, `derived/` prefix | Regenerable; tied to original | Preview, thumbnail, model-input copy | Pipeline |
| Metadata store | PostgreSQL | Per retention matrix | `observations`, `image_assets`, quality, predictions | Server |
| Backup store | Separate bucket/region | Rotation `TBD` | DB backups, object versions, model artefacts | Server |

The original and the derivative are **different objects**. Deleting a derivative never
deletes an original; deleting an original (after approval) cascades to derivatives.

---

## 2. Object layout

`05-data-layer.md` §8 defines the base layout. This document proposes one addition: an
explicit `derived/` prefix so originals and derivatives cannot be confused.

```
s3://<private-bucket>/
  observations/<yyyy>/<mm>/<observation_id>/<image_id>/
      original.<ext>                      # immutable, never modified
      derived/<pipeline_version>/
          preview.jpg                     # for the app and reviewer queue
          thumb.jpg                       # list view
          model-input-<w>x<h>.jpg         # deterministic resize for inference
  advisories/<advisory_id>/<version>/<file>
  models/<kind>/<version>/<artefact>
  exports/<export_job_id>/<file>
```

If the `derived/` prefix is not accepted, `preview.jpg` still counts as a derivative and
must be regenerable; the rule is the separation, not the exact path.

### 2.1 Storage rules

- Private bucket. No public read ACL. No directory listing.
- Access only through short-lived presigned URLs (≤ 10 minutes).
- Server-side encryption at rest; TLS in transit.
- The object key contains no farmer name, phone number or exact coordinates.
- The `image_id` is a UUID; the `storage_key` is opaque.
- Content hash (SHA-256) stored in `image_assets`.
- No object is overwritten in place. A correction creates a new object and a new record.

---

## 3. Upload flow

```
capture
  → local durable queue (encrypted if supported)
  → app obtains a presigned PUT (or multipart session) for this image_id
  → upload parts
  → server verifies size, mime (magic bytes), dimensions and checksum
  → write image_assets row (upload_status = complete)
  → strip EXIF GPS into a quarantined copy if present, then store sanitised original
  → enqueue quality gate
  → generate derivatives in derived/<pipeline_version>/
  → confirm to device; device may delete the local copy only after confirmation
```

### 3.1 Idempotency

- `client_report_id` is unique per user; re-sending the same case does not create a duplicate.
- `content_hash` detects the same image uploaded twice.
- A repeated upload of the same `image_id` returns the existing record.
- A retry after a timeout is safe; the client does not need to know whether the first
  attempt partially succeeded.

### 3.2 Validation before storage

| Check | Failure action |
|---|---|
| Magic-byte content type matches an allowlist | Reject; keep the attempt in the error log; do not store as an image |
| Byte size within limits | Reject with a clear message |
| Dimensions within limits and > 0 | Reject |
| SHA-256 matches the client-declared hash | Quarantine; do not replace the original |
| Duplicate content hash | Link to the existing image; do not store a second copy |
| Filename or metadata contains script/HTML | Treat as hostile; never render |
| Malware scan (if available) | Quarantine |

Rejected uploads are **not silently dropped**. The case remains visible to the collector with
the reason, and the event is logged.

---

## 4. EXIF and location

- GPS tags are **stripped by default** before the original is stored. The sanitised original
  is the stored original.
- If the file arrives with GPS and stripping fails, the image is **quarantined**, not used.
- Capture timestamp and orientation are preserved where needed for review; they are not PII.
- Exact coordinates, if separately consented, are stored in the database as a restricted
  field — never re-embedded in the image and never added to a presigned derivative.
- The record keeps `exif_gps_present` and `exif_stripped` so the pipeline can prove what
  happened.

---

## 5. Access control

| Actor | Original | Derivative | Presigned URL | Notes |
|---|---|---|---|---|
| Farmer (owner) | Own cases | Own cases | Yes, own case only | Cannot browse other users |
| Extension worker | Assigned area cases | Assigned area cases | Yes, scope-limited | Object-level ownership check |
| Pathologist | Assigned review cases | Assigned review cases | Yes, review-scoped | No bulk download |
| Admin | Metadata and audit | Metadata and audit | No default | Viewing a record is audited |
| Pipeline service | Read/write within its prefix | Read/write | Internal credentials | No farmer PII in logs |
| Partner | Only under a signed agreement | Only under a signed agreement | Explicit, scoped | Recorded in the dataset register |

- Authorisation is checked on every object request, not only on the listing endpoint.
- A presigned URL is a capability. It is short-lived, single-purpose and never logged as a
  credential.
- Bulk export requires role check, written purpose, row limit and an audit event.
- Removing a user's access does not delete their data; retention and deletion follow the
  procedure.

---

## 6. Original-image retention

- Originals are **immutable**. There is no update path in the application.
- Retention period: **`TBD`** — programme and legal decision (see
  `../governance/05-retention-and-deletion.md`).
- Retention is implemented with object lifecycle rules **and** a database check, so a
  lifecycle misconfiguration cannot silently delete more than intended.
- Deletion requires an approved trigger: user request, retention expiry, permission
  withdrawal, legal order, erroneous record or programme closure.
- A legal hold suspends deletion and is recorded with scope, reason, authority and review date.
- Deletion of an original cascades to derivatives and previews.
- Deletion is audited: who approved it, what was deleted, when, and the scope. The audit
  event does **not** contain the deleted image.
- Backups may retain a deleted object until the next rotation; this limitation is disclosed
  to the requester and tested in the restore drill.

### 6.1 What is never deleted

- A prediction or review row because its image was deleted. It is retained in de-identified
  form or tombstoned per policy.
- An audit event.
- A record under legal hold.
- A quarantined record without an approved resolution.

---

## 7. Derivatives

Derivatives exist to serve the app, the reviewer queue and the model. They are **not**
records of evidence.

| Derivative | Purpose | Regeneration |
|---|---|---|
| `preview.jpg` | App display, reviewer queue | From original + pipeline version |
| `thumb.jpg` | List views | From original + pipeline version |
| `model-input-<w>x<h>.jpg` | Deterministic inference input | From original + model input spec |

Rules:

- Every derivative records the `pipeline_version` and the transformation parameters.
- A derivative is never used as a label source of truth or as legal evidence.
- Deleting a derivative is always safe; it is regenerated on demand.
- Derivatives inherit the original's access rules.
- A derivative must not contain EXIF GPS or PII that was stripped from the original.
- If a derivative is found to be wrong, it is regenerated; the original is untouched.

---

## 8. Backup and restore

| Item | Mechanism | Status |
|---|---|---|
| PostgreSQL | Daily automated backup + WAL archiving where available | Not implemented |
| Object storage | Versioning enabled; delete protection via lifecycle rules | Not implemented |
| Model artefacts | Exported with each backup set, registry included | Not implemented |
| Off-site / second region | `TBD` — depends on hosting and legal review | Not decided |
| Encryption | At rest and in transit | Required |
| Restore test | Before pilot; then quarterly | Not scheduled |
| RPO / RTO | `TBD` | Not decided |

Rules:

- A backup is not a substitute for access control. Backups are encrypted and restricted.
- Restore is tested, not assumed. A backup that has never been restored is not a backup.
- Deletion propagation to backups is tested. If a deleted object reappears after a restore,
  the deletion job must run again before the environment is used.
- Backup copies do not reset retention. The retention clock follows the original creation.

---

## 9. Offline queue and no-loss rule

- The device writes the case and its images to a durable local queue before confirming
  capture.
- The queue is drained in order; a failed image does not block the rest of the case from
  retrying, but the case is not marked complete until all images are confirmed.
- The app shows the collector the queue state: pending, uploading, failed, complete.
- If storage is exhausted, the app refuses new cases and warns; it never evicts the oldest
  queued case silently.
- If the collector deletes a queued case, the app records the deletion and reports it.
- **Silent loss is a defect.** The pilot measures it and requires zero.

---

## 10. Failure handling

| Failure | Behaviour | Recorded as |
|---|---|---|
| Network drops mid-upload | Resume or restart from the last confirmed part | Upload retry |
| Checksum mismatch | Quarantine; keep the client copy; do not accept | `file_corrupt` |
| Duplicate upload | Link to existing image | `duplicate_hash` |
| Unsupported type | Reject with a message; keep the attempt | `unsupported_type` |
| Empty or truncated file | Reject; keep the attempt | `zero_bytes` |
| GPS present after stripping | Quarantine | `pii_detected` |
| Storage full | Stop accepting new cases; warn | Operability incident |
| Presigned URL expired | Request a new one; no data loss | Upload retry |
| Server error after write | Idempotent retry returns the existing record | Upload retry |

Every failure keeps the original attempt available for diagnosis. None is a silent drop.

---

## 11. Acceptance criteria

- [ ] Originals are stored once, immutably, in a private bucket.
- [ ] Derivatives live under a separate prefix and are regenerable.
- [ ] Every derivative records its pipeline version.
- [ ] Presigned URLs expire in ≤ 10 minutes and are never logged as credentials.
- [ ] EXIF GPS is absent from stored originals; a failure to strip quarantines the image.
- [ ] Duplicate uploads are linked by content hash, not stored twice.
- [ ] The device queue survives restart and connectivity loss.
- [ ] A failed upload is visible to the collector with a reason.
- [ ] Deletion cascades from original to derivatives and is audited.
- [ ] A legal hold blocks deletion.
- [ ] A restore drill is completed before the pilot.
- [ ] Deletion propagation to backups is tested.
- [ ] No object key or derivative contains farmer identity or precise location.

# Retention and deletion procedure

**Status:** Draft — retention periods are **TBD** pending legal/programme decision (D10, with D4).
**Owner:** Programme lead + legal + data engineer (TBD)
**Last updated:** 2026-11-06
**Authorities:** `final/feature-specs/05-data-layer.md` §11–12;
`final/feature-specs/03-auth-and-roles.md` §7; `final/TRD.md` §6.9.

> **Boundary:** the mechanism is implementable now; the periods are not. No period in this
> document is a legal determination. Counsel and the owning institution must approve the
> retention schedule before the pilot.

---

## 1. Principles

- Collect only what is needed for the stated purpose.
- Distinguish **unknown** from **zero**.
- Never delete silently: every deletion has a trigger, an actor and an audit record.
- Predictions, reviews, audit events and issued forecasts are not soft-deleted.
- Backups are not edited in place; deletion propagates on the next restore cycle.
- Legal hold suspends deletion.
- Demo data is labelled and never mixes with production data.

---

## 2. Retention matrix

| Data class | Examples | Retention period | Trigger | Deletion behaviour |
|---|---|---|---|---|
| User account | Phone/email, locale, status | TBD | Account deletion or programme end | Soft delete → revoke sessions → hard-delete job; retain audit and non-identifying aggregates |
| Consent events | Type, version, grant/withdraw, text hash | TBD; longer than the account | Account deletion or programme end | Retain as audit evidence unless legal order requires deletion |
| Growing area | Approximate area, optional geometry | TBD | Account deletion or programme end | Soft delete; remove precise geometry first |
| Observations and images | Reports, originals, previews | TBD | Case retention expiry or deletion request | Soft delete → hard delete; remove derivatives and previews; propagate to object storage |
| Archive originals (`ARC-###`) | Read-only archive images and metadata | Per permission record; TBD | Permission expiry, withdrawal or programme end | Return or destroy exactly as the permission requires; never delete before it allows; record evidence |
| Archive mapping and provenance | Manifests, checksums, original labels, mapping table, reviewer refs | Longer than the archive batch; TBD | Programme audit expiry | Retain as audit evidence; minimise reviewer identity where required |
| Archive quarantine | Unmappable, conflicting or provenance-missing records | TBD | Resolution plus retention expiry | Preserve the original; never delete merely because the label is unmappable |
| Image quality results | Gate version, flags, thresholds | TBD | Same as image | Retain for model audit if de-identified; otherwise delete with image |
| Image predictions | Candidates, model version, abstention | Longer than the case | Model/programme audit expiry | Append-only; retain in de-identified form; never soft-delete |
| Reviews and evidence | Decisions, notes, lab/field evidence | Longer than the case | Programme audit expiry | Append-only; retain; de-identify where required |
| Verification projection | Current status | Rebuildable | Rebuilt from review history | Derived; not a retention source of truth |
| Weather snapshots | Variables, source timestamps | TBD | Forecast reproducibility window | Archive after the configured period; never silently drop |
| Feature snapshots | Immutable features per run | Same as forecast reproducibility | Programme end or archive | Retain; referenced by forecasts |
| Forecasts | Band, coverage, drivers, lineage | TBD | Programme end or archive | Append-only; retain |
| Forecast runs | Job audit | TBD | Operational audit window | Retain |
| Advisory versions and approvals | Content, approver, validity | TBD; longer than publication | Legal/audit requirement | Retain; never serve expired content |
| Alerts and deliveries | Message version, status, provider ref | TBD | Operational audit window | Retain delivery status; minimise message content |
| Alert feedback | Rating, reason | TBD | Product review window | Retain in aggregate; minimise free text |
| Audit events | Actor, action, entity, reason | Longer than case data; TBD | Legal/audit requirement | Append-only; never hard-deleted except legal order |
| Sessions / refresh tokens | Hashed token, family | Access 15 min; refresh 30 days; family revoked on logout | Expiry or revocation | Purge by job |
| OTP codes | Hashed code | 5 min TTL; max 5 attempts | Expiry | Purge by job; never log |
| Password-reset tokens | Single-use token | 30 min TTL | Use or expiry | Purge by job |
| Presigned URLs | Temporary access link | ≤ 10 min | Expiry | Expire; no storage of the URL as a credential |
| Exports | Requested aggregate file | Short TTL; TBD | Download window | Delete after window; record deletion |
| Backups | Database and object versions | Rotation; TBD | Schedule | Retain per rotation; restore drill |
| Demo data | Synthetic fixtures | Until demo reset | Reset command | Delete or regenerate; never promote to production |

**`TBD` means the period must not be guessed.** Record the decision in the approved
retention schedule and update this table.

---

## 3. Deletion triggers

| Trigger | Who can initiate | Verification required |
|---|---|---|
| User requests account deletion | User | Identity verification; resolve/discard queued reports first |
| Consent withdrawal for optional research | User | None beyond authenticated request |
| Retention period expires | Scheduled job | Job log and row count |
| Legal/regulatory order | Legal owner | Signed instruction; legal hold check |
| Dataset permission expires or is withdrawn | Data owner | Contract record; scope of deletion |
| Archive permission expires, is withdrawn, or the institution requests return | Data owner + legal | Signed permission record; return/destruction instruction; legal-hold check |
| Erroneous or quarantined record | Data owner | Quarantine resolution record |
| Demo reset | Engineering | Environment check; `is_demo` confirmation |
| Programme closure | Programme lead | Approved closure plan |

---

## 4. Deletion workflow

```
request or trigger
  → verify identity / authority
  → check legal hold
  → identify all related records and objects
  → resolve queued reports (sync or explicitly discard)
  → revoke sessions and tokens
  → mark deleted_at (user-facing entities)
  → schedule hard delete
  → delete object-store originals, derivatives and previews
  → delete or de-identify dependent records per policy
  → retain audit and non-identifying aggregates
  → record completion, scope and exceptions
  → verify with a sample query
```

Rules:

- A deletion request must not silently destroy an open review; the user is warned and
  must resolve or explicitly discard queued reports.
- A case under legal hold is not deleted; the requester is told the reason where lawful.
- Predictions, reviews and audit rows are retained in de-identified form unless a legal
  order requires otherwise.
- Deletion from primary storage does not immediately remove backup copies; the next
  restore cycle must apply the same deletion. This limitation must be disclosed.
- Every deletion writes an audit event without copying the deleted content.

---

## 5. Backups and restore

- Daily PostgreSQL backup; WAL archiving where available.
- Object-storage versioning enabled.
- Restore tested before pilot; RTO/RPO documented.
- Model artefacts and the registry are included in the backup set.
- Quarterly restore drill; result recorded.
- Deletion propagation is tested, not assumed.

---

## 6. Legal hold

- A hold suspends deletion for the named records or datasets.
- The hold records: scope, reason, authority, start date, review date and owner.
- The hold is lifted only by the legal owner.
- Holds are audited.

---

## 7. Verification and reporting

- Monthly check: records past retention that remain undeleted.
- Monthly check: deletion jobs that failed.
- Quarterly check: backup restore and deletion propagation.
- Report counts and exceptions to the programme lead; never include PII.
- Metrics: deletion requests completed on time, failed deletion jobs, legal holds,
  quarantine backlog.

---

## 8. Open decisions

1. Retention period for observations and images.
2. Retention period for predictions, reviews and audit events.
3. Forecast/feature snapshot reproducibility window.
4. Export file TTL.
5. Backup rotation and the RTO/RPO for the pilot.
6. Whether de-identified data may be retained for research after account deletion.
7. The exact lawful basis and notice wording for retention.
8. The deletion SLA and communication template.
9. Whether users can request deletion of individual images while keeping the case.
10. Cross-border backup locations and transfer mechanism.
11. Archive retention period, return/destruction obligations and the evidence required.
12. Whether reviewer identity in archive provenance is retained, minimised or deleted
    after the audit window.

---

## 9. Change log

| Date | Change | Owner |
|---|---|---|
| 2026-11-06 | Initial procedure drafted; periods TBD | Draft — legal/data engineer (TBD) |
| 2026-11-06 | Added archive originals, mapping/provenance and archive-quarantine rows plus archive deletion trigger; periods still TBD | Draft — legal/data engineer (TBD) |

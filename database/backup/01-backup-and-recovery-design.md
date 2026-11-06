# 01 — Backup, Disaster Recovery and Restore Design

**Status:** Approved Engineering Architecture  
**Authority:** `final/feature-specs/05-data-layer.md` §12; `database/collection/04-secure-upload-and-retention.md` §8; `final/TRD.md` §6.  
**Owner:** Infrastructure / Platform Lead & Data Engineer  

---

## 1. Objectives and SLOs

The system is a regional agricultural decision-support platform operating in mission-critical field conditions. Backup and recovery procedures guarantee data durability, auditability, and legal compliance.

| Metric | Target | Rationale |
|---|---|---|
| **RPO (Recovery Point Objective)** | **≤ 15 minutes** | Point-in-time recovery via continuous WAL archiving minimizes loss of active field reports. |
| **RTO (Recovery Time Objective)** | **≤ 2 hours** | Database restored, migrations verified, and core API health confirmed within 120 minutes. |
| **Object Storage RPO** | **0 seconds** | S3 cross-region replication + bucket versioning ensures instant multi-zone survival. |
| **Backup Retention Period** | **30 days (rolling)** | Daily snapshots retained for 30 days, monthly snapshots retained for 1 year in cold archive. |

---

## 2. Backup Architecture by Storage Layer

```
┌────────────────────────────────┐         ┌───────────────────────────────┐
│     PostgreSQL 16 Primary      │         │   Object Storage (S3 / GCS)   │
│  (Relational Data + PostGIS)   │         │  (Originals, Derivatives,     │
└───────────────┬────────────────┘         │   Model Artefacts, Exports)   │
                │                          └───────────────┬───────────────┘
     Continuous │ Daily Base                               │ Cross-Region
     WAL Stream │ Snapshot (pgBackRest)                    │ Replication
                ▼                                          ▼
┌────────────────────────────────┐         ┌───────────────────────────────┐
│    Encrypted Backup Storage    │         │ Secondary DR Storage Bucket   │
│     (Isolated S3 Bucket)       │         │    (Separate AWS Account)     │
└────────────────────────────────┘         └───────────────────────────────┘
```

### 2.1 PostgreSQL 16 + PostGIS Archival
* **Tooling:** `pgBackRest` or `wal-g` with multi-threaded compression (lz4 or zstd).
* **Base Backups:** Full synthetic/physical base backup taken every 24 hours at 01:00 UTC during off-peak field activity.
* **Continuous WAL Archiving:** WAL segments pushed to private backup bucket within 60 seconds of completion or via 15-minute archive timeout (`archive_timeout = 900s`).
* **Encryption:** Client-side AES-256 encryption before transmission (`pgbackrest` cipher-type `aes-256-cbc`). Backup encryption keys managed in KMS and rotated annually.

### 2.2 Object Storage (Originals & Models)
* **S3 Bucket Versioning:** Enabled permanently on `s3://<private-bucket>`. Overwrites and deletions create delete markers rather than expunging data.
* **S3 Object Lock / WORM:** Enabled in Compliance Mode for `observations/.../original.<ext>` and `models/...` with a retention hold matching the legal retention policy.
* **Cross-Region Replication (CRR):** Real-time asynchronous replication from Primary Region (e.g., `ap-south-1` Mumbai) to Disaster Recovery Region (e.g., `ap-south-2` Hyderabad).

### 2.3 Model Registry and Lineage Bundling
A database restore alone is insufficient if model weights are desynchronized. Every backup set includes:
1. Dump of `model_registry` table.
2. Direct manifest of active model artefacts in `models/<kind>/<version>/`.
3. Cryptographic SHA-256 checksum verification linking `model_registry.checksum` to S3 stored weights.

---

## 3. Deletion Propagation and Privacy Compliance (DPIA)

When a user exercises their right to erasure or retention expires (`governance/05-retention-and-deletion.md`):
1. **Live State:** Database record marked with `deleted_at`, image original deleted from S3, and derivatives pruned.
2. **Backup Disclosures:** Backups are immutable point-in-time archives and cannot be edited selectively without invalidating the cryptographic chain.
3. **Re-emergence Prevention (Tombstone Replay):**
   * All deletion events write an immutable tombstone into `audit_events` with `action = 'data_erasure'`.
   * **Post-Restore Protocol:** Following any disaster recovery database restoration from backup, the automated recovery pipeline executes `scripts/replay_deletion_tombstones.py`. This script reads the secondary audit store and re-executes purges for any records deleted after the restored backup was taken.

---

## 4. Quarterly Restore Drill Runbook

A backup that has never been restored is an unverified assumption. A mandatory quarterly drill is executed in a dedicated staging sandbox.

### Step-by-Step Restoration Drill

```
1. Provision Isolated Sandbox VPC & Clean Postgres Instance
   ↓
2. Fetch Latest Base Backup + WAL Stream from Backup Bucket
   ↓
3. Execute Point-in-Time Restore (PITR) to Target Recovery Time
   ↓
4. Run Alembic Database Health Check (`alembic check` / `alembic upgrade head`)
   ↓
5. Execute Integrity Verification Suite (`python3 database/backup/verify_backup.py`)
   ↓
6. Validate Read/Write Sanity & PostGIS Query Functionality
   ↓
7. Run Tombstone Replay & Verify Erased Records Remain Deleted
   ↓
8. Log Completion, Measured RTO and Checksums in `progress-tracker.md`
   ↓
9. Teardown Sandbox Infrastructure
```

---

## 5. Automated Health Checks and Alerting

* **Backup Failure Alarm:** Triggers P1 alert to on-call engineer if:
  * WAL archiving fails for > 3 consecutive segments or 30 minutes.
  * Daily base backup does not complete by 04:00 UTC.
  * S3 cross-region replication latency exceeds 15 minutes.
* **Integrity Validation:** Every automated daily backup triggers an automated container job that restores the backup into a temporary Postgres container and executes `SELECT count(*) FROM users`.


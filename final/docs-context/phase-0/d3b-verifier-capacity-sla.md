# D3b — Verifier capacity, triage and review SLA

**Decision ID:** D3b (closes the capacity/SLA part of D3)
**Status:** `[x]` Recorded 2026-11-06 — partner staffing and named holders confirmed by MoU.
**Owner:** Programme lead, with the partner field operations lead.
**Needs by:** Gate 0 for staffing; Gate 5 for operational evidence.
**Parent decision:** D3 — extension-worker-first verification; `confirmed` requires the
scoped `can_confirm` permission; `admin` does not verify
([ADR-010](../adr/0010-v1-roles.md)).

> **What this does not claim.** The case volumes below are **planning assumptions** for a
> six-hobli pilot, not measured demand. The first four weeks of the silent phase measure
> actual arrival rate and review time. Staffing is adjusted to the measured queue; the
> review standard is not relaxed to clear a backlog.

---

## 1. Decision

The pilot uses an **extension-worker-first tiered review model** with a named accountable
holder at each tier.

| Tier | Who | Permission | May set | May not set |
|---|---|---|---|---|
| T1 — triage reviewer | Trained extension worker / plant-clinic staff | `extension_worker` | `probable`, `rejected`, `duplicate`, `needs_visit`, `unresolved`; request a better image | `confirmed` |
| T2 — confirming reviewer | Named `can_confirm` holder (senior extension officer or plant-clinic agronomist) | `extension_worker` + `can_confirm` | All T1 states + `confirmed`; correct a label with a revision note | Change roles, approve advisory content |
| T3 — escalation | District agronomist / pathologist, reached through T2 | External expert, no routine app login | Written second opinion recorded by T2 | Direct database edits |
| Governance | Admin | `admin` | User/role/configuration administration | Any verification status (separation of duties) |

**Minimum capacity per pilot area (hobli/block):**

- 2 named `can_confirm` holders, at least one reachable on each working day.
- 4 trained T1 reviewers across the six pilot sites (shared pool is acceptable if the
  area-scoping rule is recorded).
- 1 named field operations lead for the district cluster.
- 1 named advisory approver holding `can_approve_advisory`; this may be the same person as a
  `can_confirm` holder only if the separation-of-duties review approves it.

**Workload and SLA:**

| Metric | Standard case | High-priority case |
|---|---|---|
| First triage (T1) | ≤ 24 h from sync | ≤ 8 h from sync |
| Confirmation decision (T2) | ≤ 48 h from triage | ≤ 24 h from triage |
| Escalation to T2 | ≤ 24 h if T1 cannot confirm | ≤ 8 h |
| Escalation to T3 | ≤ 72 h after T2 request | ≤ 48 h |
| Reviewer workload cap | 15 cases/day and 60 cases/week per T1 reviewer | Included in the cap |
| `can_confirm` workload cap | 30 cases/day and 120 cases/week per holder | Included in the cap |
| Queue health review | Weekly | Immediate if backlog > 40 open cases or median first triage > 24 h |

The 48-hour confirmation SLA is a **pilot service target**. It is not a clinical guarantee
and does not convert an unverified report into a confirmed case.

---

## 2. Triage rules

Cases enter the queue sorted by a transparent priority score. The score is computed from
recorded fields, not reviewer intuition alone.

| Priority | Trigger (any one) | Target response |
|---|---|---|
| **P0 — urgent** | Suspected late blight in a block with a current moderate/high outlook; cluster of ≥ 3 reports of the same target in one block within 7 days; a report from a block with no `can_confirm` coverage | T1 ≤ 4 h; T2 ≤ 12 h |
| **P1 — high** | Crop at flowering/fruiting; suspected early blight or Septoria with ≥ 25% leaf area affected; image quality passes but the model abstains; farmer requested expert review | T1 ≤ 12 h; T2 ≤ 24 h |
| **P2 — standard** | All other eligible reports | T1 ≤ 24 h; T2 ≤ 48 h |
| **P3 — hold** | Duplicate, unusable image, missing required consent, outside the allowlist | Close or return to sender with a reason; no disease label |

**Rules:**

- The queue shows age, priority, crop stage, block, target guess, image-quality flags and
  prior reviews. It never shows a single "diagnosis" that a reviewer can accept with one
  click.
- A T1 reviewer who lacks `can_confirm` must escalate; they may not mark `confirmed`.
- A `confirmed` decision requires at least one piece of recorded evidence (symptom
  description, field observation, or a second reviewer opinion) from the target reference
  sheet.
- `needs_visit` is a valid outcome and does not count as a failure.
- Every state change writes an append-only review event and an audit event.

---

## 3. Escalation path

```
Farmer / field staff report
        │
        ▼
T1 triage reviewer  ── cannot confirm ──►  T2 named can_confirm holder
        │                                      │
        │                                      ├─ confirm / reject / needs visit
        │                                      │
        └─ duplicate / unusable / consent ─────┘
                                               │
                                     unresolved or high-impact
                                               ▼
                                  T3 district agronomist / pathologist
                                               │
                                     written opinion recorded by T2
                                               ▼
                                  Programme lead (safety/trust escalation)
```

**Named-holder rule:** a named holder is a person recorded in the partner register with a
start date, area, permission scope and backup. A role title alone is not a named holder.
Until names are recorded, the pilot cannot start the limited-alert phase.

---

## 4. Compensation and workload protection

- Reviewer time is compensated through the partner MoU; the pilot does not rely on unpaid
  expert labour (R-15).
- The budget includes a named line for T1/T2 review time, training and backfill.
- A reviewer may decline a case that exceeds their competence; the case escalates without
  penalty.
- No reviewer is asked to meet a volume target that requires lowering the evidence standard.
- Weekly queue review adjusts staffing, case routing and training, not the definition of
  `confirmed`.

---

## 5. Capacity model (planning assumption)

| Input | Low | Expected | High |
|---|---:|---:|---:|
| Eligible reports/day across six sites | 20 | 50 | 90 |
| T1 capacity at 15 cases/day × 4 reviewers | 60 | 60 | 60 |
| T2 capacity at 30 cases/day × 2 holders | 60 | 60 | 60 |
| T1 utilisation at expected volume | 33% | 83% | 150% |
| T2 utilisation at expected volume | 33% | 83% | 150% |

At the high scenario the queue breaches the SLA. The response is to add a fifth T1 reviewer
and a third `can_confirm` holder, or to narrow intake to P0/P1 cases. It is **not** to
auto-confirm or skip review.

---

## 6. Failure paths

| Failure | Required behaviour |
|---|---|
| No `can_confirm` holder available in an area | Cases remain `probable`/`unresolved`; the area is flagged as verification-limited; limited alerts for that area pause |
| Backlog > 40 open cases | Programme lead notified; intake triage tightened; daily stand-up until cleared |
| Median first triage > 24 h for 3 consecutive days | Staffing review; P2 queue may be delayed with a visible status, never silently dropped |
| Reviewer conflict of interest | Reassign; record the reason in the audit event |
| Suspected safety issue in a confirmed case | P0 escalation to programme lead and advisory approver; alert type paused pending review |
| Reviewer leaves mid-season | Backup holder takes over; permission revoked same day; audit records the change |

---

## 7. Evidence required at Gate 0

- [ ] Partner has nominated the T1 reviewers and two `can_confirm` holders per pilot area.
- [ ] Names, areas, permissions, start dates and backups are recorded in
      [`partner-and-data-permission-register.md`](partner-and-data-permission-register.md).
- [ ] Compensation line is in the budget.
- [ ] The partner has accepted the 48-hour confirmation SLA and the escalation path.
- [ ] Training plan and calibration round are scheduled before the first alert.

**Sign-off**

| Role | Name | Decision | Date |
|---|---|---|---|
| Programme lead | TBD at workshop | Pending | — |
| Partner field operations lead | TBD at MoU | Pending | — |
| `can_confirm` holder (area 1) | TBD at MoU | Pending | — |
| `can_confirm` holder (area 2) | TBD at MoU | Pending | — |

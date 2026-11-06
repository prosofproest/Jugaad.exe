# 04 — Expert review

**Status:** Draft
**Owner:** Product lead + agronomist (TBD)
**Depends on:** `02-reporting-and-capture.md`, `03-auth-and-roles.md`, `05-data-layer.md`
**Implements:** review queue, triage, case detail, verification state machine, evidence,
label correction, escalation, audit.

---

## 1. Goal

Turn user reports into trustworthy verified evidence without creating an unreviewable
backlog. Review is the bottleneck of the whole system: if it fails, the verified map layer
and the forecast track both fail silently.

Design principle: **triage before depth**. A reviewer should be able to decide most cases
in under two minutes, and escalate the rest with full context preserved.

---

## 2. Roles in this feature

| Role / permission | Can do |
|---|---|
| `extension_worker` | Work assigned area queue; set `probable`, `needs_visit`, `duplicate`, `rejected`, `unresolved`; request confirmation from a `can_confirm` holder |
| `extension_worker` + `can_confirm` | All extension actions + `confirmed`, label correction, severity, lab evidence, taxonomy questions |
| `extension_worker` + `can_approve_advisory` | Approve advisory content for the area (second approver for high-risk content) |
| `admin` | Configure queue rules and SLA; reassign; grant `can_confirm` / `can_approve_advisory`; **cannot** set verification status |

`can_confirm` and `can_approve_advisory` are scoped permissions, not roles (ADR-010). If
no account in an area holds `can_confirm`, cases stop at `probable` and the queue shows a
visible "no confirmer in area" warning.

---

## 3. Review flow

```
Queue (triage)
  ├─ filters: area, crop, target, age, urgency, status, assigned-to-me
  ├─ sort: urgency → uncertainty → age
  └─ open case
       ├─ Evidence: original image(s), metadata, quality flags, model candidates,
       │            assessment version, forecast context at report time
       ├─ Field context: crop, stage, area (approximate), notes, prior cases
       ├─ Contact: request better image / request field details (logged)
       └─ Decision
            ├─ confirmed        (`can_confirm` only; evidence required)
            ├─ probable         (evidence required)
            ├─ rejected         (evidence required; reason code)
            ├─ duplicate        (link to canonical case)
            ├─ needs_visit      (assign field visit; reason required)
            └─ unresolved       (insufficient evidence; reason required)
                 └─ optional: correct label, severity, field observations,
                              lab confirmation (separate evidence tier)
```

---

## 4. Verification state machine

```
                 ┌────────────► confirmed ◄──── (`can_confirm` only)
                 │                  │
pending_review ──┼────────────► probable
                 │                  │
                 ├────────────► rejected
                 │                  │
                 ├────────────► duplicate ──► link to canonical observation
                 │                  │
                 ├────────────► needs_visit ──► (visit recorded) ──► confirmed|probable|rejected
                 │                  │
                 └────────────► unresolved ──► (new evidence) ──► any terminal state
```

Rules:

- `pending_review` is the default for every submitted report; model output never changes it.
- Transitions are server-enforced; the client receives the allowed next states.
- `confirmed` requires the `can_confirm` permission **and** at least one evidence item.
- `duplicate` requires a canonical observation reference.
- Every transition appends to `review_events`; the current status is a projection.
- Re-opening a decided case requires a reason and creates a new review event; history is
  never overwritten.
- A model prediction may be shown beside a decision but is never copied into it.

---

## 5. Triage rules

Urgency is computed server-side from configuration, not hard-coded:

```
urgency = f(severity_hint, model_uncertainty, age, crop_value, area_risk, duplicate_signal)
```

| Signal | Effect |
|---|---|
| High-severity symptom hint | Raise |
| Model abstained or low confidence | Raise (needs human eyes) |
| Age > SLA | Raise; mark overdue |
| Same area/target cluster | Group; review together |
| Probable duplicate (image hash / near-duplicate) | Lower; suggest merge |
| Low-quality image | Lower for diagnosis, raise for "request retake" |

Queue views:

- **My area** (default for extension workers).
- **Escalations** (`can_confirm` holders and area leads).
- **Overdue** (any role, read-only for non-owners).
- **Unassigned** (admin/lead).

Workload caps: a reviewer sees a daily cap from config; when reached, new items route to
the next reviewer or stay unassigned. The cap exists to prevent silent backlog growth.

---

## 6. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-04-01 | Queue supports filter by area, crop, target, age, status, assignee, urgency | MUST |
| FR-04-02 | Default sort is urgency → uncertainty → age, with stable tie-breaking | MUST |
| FR-04-03 | Reviewer can claim/unclaim a case; assignment is audited | MUST |
| FR-04-04 | Case detail shows original image(s) at full resolution, metadata, quality flags, candidates, model version, forecast context at report time | MUST |
| FR-04-05 | Case detail shows prior cases from the same area/user (privacy-scoped) | SHOULD |
| FR-04-06 | Reviewer can request a better image or more field detail; request is logged and visible to the farmer | MUST |
| FR-04-07 | Reviewer records one decision from the server-provided state list | MUST |
| FR-04-08 | Required evidence enforced per decision type | MUST |
| FR-04-09 | `can_confirm`-gated transitions enforced server-side | MUST |
| FR-04-10 | Label correction records previous label, new label, reviewer, reason | MUST |
| FR-04-11 | Severity recorded using crop-specific criteria, not a generic scale | SHOULD |
| FR-04-12 | Lab confirmation is a separate, optional evidence tier | SHOULD |
| FR-04-13 | Duplicate decision links to a canonical case and merges counts correctly | MUST |
| FR-04-14 | Every decision writes an immutable review event + audit event | MUST |
| FR-04-15 | Queue shows backlog, median age and overdue count | MUST |
| FR-04-16 | Re-opening a decided case requires a reason | MUST |
| FR-04-17 | Case is locked while another reviewer is editing; lock expires | MUST |
| FR-04-18 | Reviewer can escalate to a `can_confirm` holder with a note | MUST |
| FR-04-19 | Verified projection updates atomically with the decision | MUST |
| FR-04-20 | Reviewer cannot see precise farm coordinates unless role permits | MUST |

---

## 7. Evidence requirements

| Decision | Minimum evidence |
|---|---|
| `confirmed` | `can_confirm` permission + image review note + (field observation or lab evidence) |
| `probable` | Image review note + at least one supporting observation |
| `rejected` | Reason code (`not_a_plant`, `healthy`, `abiotic`, `different_pest`, `poor_image`, `other`) + note |
| `duplicate` | Canonical observation ID |
| `needs_visit` | Reason + requested visit window |
| `unresolved` | Reason (`poor_image`, `conflicting_signs`, `no_field_access`, `other`) + note |

Evidence is structured where possible (codes) plus a short free-text note. Free text is
never used as the only evidence for `confirmed`.

---

## 8. Case detail content

Required blocks, in order:

1. **Header:** case ID, crop, area, submitted time, current status, SLA/overdue.
2. **Image:** original at full resolution, zoom, quality flags, capture metadata.
3. **Model view:** candidates with qualitative confidence, abstention state, model
   version, generated time, "not a diagnosis" reminder.
4. **Context:** growth stage, variety, notes, prior cases, forecast at report time
   (clearly labelled as area-level).
5. **History:** submissions, review requests, prior decisions, corrections.
6. **Decision panel:** allowed decisions, required evidence, submit.

Do not hide model limitations behind a tooltip; they belong in the model block.

---

## 9. API touchpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v1/reviews/queue` | Filtered, sorted, paginated queue |
| `GET` | `/v1/reviews/queue/summary` | Backlog, median age, overdue, by area |
| `POST` | `/v1/reviews/{observation_id}/claim` | Claim/unclaim |
| `GET` | `/v1/reviews/{observation_id}` | Case detail + allowed transitions |
| `POST` | `/v1/reviews/{observation_id}/decisions` | Record decision |
| `POST` | `/v1/reviews/{observation_id}/escalate` | Escalate to a `can_confirm` holder |
| `POST` | `/v1/reviews/{observation_id}/request-info` | Ask farmer for retake/details |
| `GET` | `/v1/reviews/{observation_id}/events` | Immutable history |

### Decision request

```json
{
  "decision": "probable",
  "corrected_label": "late_blight",
  "severity": "moderate",
  "evidence": {
    "image_note": "Lesions with pale green halo on lower leaves",
    "field_observation": "Spread across 3 of 10 inspected plants",
    "lab_confirmation": null
  },
  "reason_code": null,
  "note": "Consistent with early late-blight symptoms; field visit advised",
  "client_request_id": "6b1f0f0e-..."
}
```

Response returns the new status, the appended event ID and the updated verified projection
version.

---

## 10. Data model touchpoints

- `reviews`: observation_id, reviewer_id, decision, reason_code, note, corrected_label,
  severity, created_at (append-only).
- `review_evidence`: review_id, type (`image_note`, `field_observation`, `lab_result`),
  value, source, created_at.
- `review_events`: immutable transition log (from, to, actor, reason, timestamp).
- `observation_verification`: current projection (status, verified_at, verified_by,
  evidence_tier) — derived, rebuildable.
- `review_assignments`: observation_id, user_id, area_code, assigned_at, expires_at.
- `review_requests`: requester, reason, status.
- `user_area_assignments`: area-scoped access.

---

## 11. Edge cases

| Case | Behaviour |
|---|---|
| Two reviewers open the same case | Soft lock on first open; second sees read-only + "claimed by X" |
| Reviewer's role changes mid-edit | Submit rejected with `forbidden`; draft preserved locally |
| Duplicate submitted before canonical decided | Link allowed; canonical may be `pending_review`; counts recalculated |
| Farmer deletes account with open case | Case anonymised, review continues on evidence; no PII retained |
| Image missing/corrupt in storage | Decision blocked; `request-info` path; incident logged |
| Model version no longer available | Case shows stored prediction snapshot; no re-run required |
| Case re-opened after verification | New event appended; verified projection recomputed; forecast feature uses latest |
| Reviewer exceeds daily cap | New items not assignable; backlog visible to lead |
| Area boundary version changes | Case keeps original boundary version; queue filter uses current, with note |

---

## 12. Non-functional requirements

| Area | Requirement |
|---|---|
| Queue latency | p95 < 1.5 s for first page on pilot data volume |
| Image view | Full-resolution load < 3 s on office broadband; progressive preview |
| Locking | Soft lock TTL 15 min, heartbeat refresh |
| Audit | Decision write and audit event in the same transaction |
| Availability | Review available during field hours; read-only degradation acceptable |
| Accessibility | Keyboard-only decision flow; screen-reader labels; focus management |
| Security | No cross-area data in queries; exports audited |

---

## 13. Acceptance criteria

- [ ] Queue default sort is urgency → uncertainty → age, with a documented formula.
- [ ] An extension worker sees only their assigned area.
- [ ] An extension worker without `can_confirm` cannot submit `confirmed` (403) — tested.
- [ ] An extension worker with `can_confirm` can submit `confirmed` — tested.
- [ ] `confirmed` without evidence is rejected by the server — tested.
- [ ] A decision writes exactly one review event and one audit event.
- [ ] `duplicate` requires a valid canonical ID and updates aggregate counts.
- [ ] Model candidates are never copied into the decision automatically.
- [ ] Concurrent edit is prevented by a soft lock with expiry.
- [ ] Re-opening a case requires a reason and preserves history.
- [ ] Backlog, median age and overdue counts match the underlying data.
- [ ] A verified decision updates the forecast-visible projection atomically.
- [ ] No precise coordinates are exposed to a role without permission.

---

## 14. Telemetry and audit

Events: `review.claimed`, `review.decision_recorded`, `review.escalated`,
`review.info_requested`, `review.reopened`, `review.lock_expired`,
`review.queue_overdue`.

Metrics: queue depth, median time-to-review, overdue rate, decisions per reviewer per day,
escalation rate, duplicate rate, correction rate, backlog trend.

---

## 15. Out of scope

- Multi-reviewer consensus scoring.
- Reviewer performance ranking.
- Automated pre-labelling of the queue.
- In-app chat with farmers (request-info is asynchronous and structured).
- Field-visit scheduling integration.

---

## 16. Open questions

1. What is the daily review capacity per extension worker, and what SLA is realistic? (D3b)
2. Does `probable` count as verified for forecast features, or only `confirmed`?
   (Recommendation: both, with an evidence tier; `unverified` never counts.) (D7)
3. Which `extension_worker` accounts should receive `can_confirm` in each pilot area, and
   how is that permission revoked when someone leaves? (D3b)
4. Is a lab-confirmation integration in scope, or only manual entry of a result?

---

## 17. Blueprint traceability

| Blueprint chapter | Where this spec uses it |
|---|---|
| 16 — Expert review portal | Whole spec |
| 20 — Image labelling protocol | §7 evidence requirements, §10 review evidence |
| 24 — Historical records and verification tiers | §4 state machine, §10 projection |
| 45 — Testing strategy | §13 acceptance criteria |
| App. D — Database entity checklist | §10 data model touchpoints |
| App. F — Example test cases | §13 acceptance criteria |

The rule that a model output is never copied into a decision comes from
`../docs-context/AGENTS.md` R4. The rule that `confirmed` needs the `can_confirm` permission
and structured evidence is enforced in the database and service layers
(`05-data-layer.md` §5, ADR-010).

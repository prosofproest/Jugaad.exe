# 07 — Advisory and alerts

**Status:** Draft
**Owner:** Agronomist + product lead (TBD)
**Depends on:** `03-auth-and-roles.md`, `05-data-layer.md`, `06-forecast-and-risk-map.md`
**Implements:** approved non-chemical guidance, advisory retrieval, alert trigger policy,
deduplication, delivery, feedback.

---

## 1. Goal

Deliver safe, locally approved guidance and timely alerts without creating a legal
liability surface or alert fatigue.

**Two hard constraints:**

1. Advisory content is **curated and approved**, never generated. No LLM writes or rewrites
   advisory text.
2. No pesticide, herbicide, fungicide or fertiliser product names, doses, mixtures,
   intervals or legal-use instructions appear anywhere in the product.

---

## 2. Advisory content model

| Field | Required | Notes |
|---|---|---|
| `crop_code` | yes | Supported crop only |
| `target_code` | yes | Supported target |
| `geo_scope` | yes | Area codes or "all supported areas" |
| `language` | yes | English or Kannada; both required before public launch |
| `season` / `valid_from` / `valid_to` | yes | Expiry is mandatory |
| `title` | yes | Plain language, no alarmism |
| `body` | yes | Structured sections, see below |
| `action_types` | yes | From the allowed list |
| `author_id` | yes | Named agronomist |
| `approver_id` | yes | Second qualified holder of `can_approve_advisory` |
| `source` | yes | Institutional source / reference |
| `version` | yes | Immutable version per edit |
| `content_hash` | yes | Detects unauthorised edits |

### Body structure

```
1. What this is about       (target, crop, area, time window)
2. What you may see         (symptoms in plain language)
3. What to do now           (non-chemical actions)
4. What not to assume       (not a diagnosis / not a confirmed outbreak)
5. When to escalate         (expert review, extension visit)
6. Source and approval      (who approved, when, valid until)
```

### Allowed action types

- `scout` — inspect plants across the field, record what you see.
- `monitor` — repeat observation over a defined period.
- `sanitise` — remove and dispose of affected plant material per local practice.
- `crop_management` — spacing, irrigation, nutrition practices approved locally.
- `escalate` — request expert review or field visit.
- `record` — keep a photo/record for comparison.

### Prohibited content (validator-enforced)

| Pattern | Example | Result |
|---|---|---|
| Product names | "apply [brand] 2 ml/L" | Reject |
| Dose / concentration | "2 g per litre", "250 ml/acre" | Reject |
| Mixture instructions | "mix with …" | Reject |
| Application interval | "spray every 7 days" | Reject |
| Pre-harvest interval | "PHI 14 days" | Reject |
| Legal-use claim | "approved for use on …" | Reject |
| Guarantee | "will prevent", "guaranteed" | Reject |
| Diagnosis claim | "this confirms …" | Reject |
| Outbreak claim | "outbreak confirmed" | Reject |

The validator is code with tests, not a style guide. Any rejected content is a release
blocker until reworded.

---

## 3. Approval workflow

```
draft (author)
  → agronomic review (agronomist or senior extension worker)
  → approval by a second holder of `can_approve_advisory`
  → published (served, versioned, expiry set)
  → expired (no longer served; retained for audit)
```

Rules:

- Author cannot be the sole approver.
- Approval requires the `can_approve_advisory` permission (ADR-010); the role alone is not
  sufficient.
- Every edit creates a new version; published versions are immutable.
- Changing content requires re-approval and a new version.
- Expiry is mandatory; the API never serves expired content.
- Approval records who, when, role and notes.
- A withdrawal (safety issue) immediately unpublishes all versions of that advisory and
  records the reason.

---

## 4. Advisory retrieval

### `GET /v1/advisories?crop=&target=&geo=&language=`

Response includes only currently valid, approved content for the requested scope. If none
exists:

```json
{
  "items": [],
  "fallback": {
    "message": "No approved advisory is available for this crop and area yet.",
    "next_step": "request_expert_review"
  }
}
```

Never substitute generic web content or generated text for a missing advisory.

---

## 5. Alert policy

Alerts are generated from forecasts, not from raw reports. Trigger requires **all** of:

1. `risk_band` ≥ configured minimum for the area/target.
2. `coverage` ≥ configured minimum.
3. Forecast freshness within threshold (`is_stale = false`).
4. An approved, valid advisory exists for the same crop/target/scope.
5. Alert policy is active and approved.
6. User has opted in to the channel.

### Deduplication

- `dedupe_key = hash(geo_code, target_code, band, window_from, window_to)`.
- One alert per key; repeated generation does not resend.
- Escalation from `moderate → high` within the same window sends a new alert with an
  explicit "updated" label; downgrades do not alert.

### Cooldown

- Per area + target + channel, configurable by severity.
- A cooldown suppresses delivery, not generation; the alert row records `suppressed`.
- No more than one alert per user per area per target per cooldown window.

---

## 6. Channels

| Channel | Use | Notes |
|---|---|---|
| In-app | Primary channel for signed-in web and mobile users | Always available; full advisory detail |
| SMS | Optional farmer reach where a gateway is available | Short template; no links required |
| Email | Staff and institutional recipients | Full advisory; opt-in |
| WhatsApp | Deferred post-v1 | Not built in v1 |
| Push | Deferred post-v1 | Not built in v1 |
| IVR | Deferred unless the partner mandates it | Out of v1 |

**Channel decision (D15, 2026-11-06):** in-app is mandatory; email is for staff; SMS is
optional per pilot partner; WhatsApp, push and IVR are deferred. The adapter interface is
built in v1 so SMS can be switched on without a schema change.

Rules:

- One message = one crop, one target, one area, one window.
- Character limits respected per channel; the full advisory is not sent by SMS.
- Push delivery is out of v1; the mobile app shows in-app alerts on next open and relies on
  foreground/background refresh, not silent push.
- Every message includes: area, crop, target, valid period, reason, next action, coverage,
  issue time, and "this is an early warning, not confirmation".
- No attachments, no image links, no product recommendations.
- Language matches the user's preference (English or Kannada); fall back to English when a
  translation is missing, and never machine-translate advisory content.

### Template (SMS, illustrative)

```
[Area] [Crop]: [BAND] risk of [target] from [date] to [date].
Reason: [driver summary]. Data coverage: [coverage].
This is an early warning, not confirmation of disease in your field.
Next: [approved non-chemical action]. Advisory v[version].
```

The template is versioned and approved; placeholders are filled from structured fields,
never free text from a model.

---

## 7. Delivery and feedback

- Delivery status per recipient: `queued`, `sent`, `delivered`, `failed`, `suppressed`,
  `opted_out`.
- Provider receipts reconciled by job; failures retried with backoff.
- Bounce/invalid number handling: mark and stop retrying after a configured limit.
- User feedback: "useful / not useful / inaccurate" plus optional reason.
- Acknowledgement is optional and does not affect future alerts.
- Preference changes are immediate for the next dispatch.

---

## 8. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-07-01 | Advisory CRUD with immutable versions and mandatory approval | MUST |
| FR-07-02 | Content validator rejects all prohibited patterns, with tests | MUST |
| FR-07-03 | Retrieval returns only approved, valid, in-scope content | MUST |
| FR-07-04 | Missing advisory returns a fallback message + escalation, never generated text | MUST |
| FR-07-05 | Alert trigger enforces band, coverage, freshness, advisory, policy, opt-in | MUST |
| FR-07-06 | Dedupe key prevents repeat alerts for the same window | MUST |
| FR-07-07 | Severity-specific cooldowns suppress delivery | MUST |
| FR-07-08 | Every message contains area, crop, target, window, reason, action, coverage, issue time | MUST |
| FR-07-09 | Message states "early warning, not confirmation" | MUST |
| FR-07-10 | Delivery status and provider receipts recorded | MUST |
| FR-07-11 | Users can opt out per channel and per target | MUST |
| FR-07-12 | Feedback captured and reportable | MUST |
| FR-07-13 | Expired advisories are never served or referenced in new alerts | MUST |
| FR-07-14 | Alert templates are versioned and approved | MUST |
| FR-07-15 | Admin can pause all alerts for an area/target immediately | MUST |

---

## 9. Data model touchpoints

- `advisories`, `advisory_versions`, `advisory_approvals` (see `05-data-layer.md`).
- `alert_policies`: geo, target, min_band, min_coverage, cooldown, channels, approver.
- `alerts`: forecast_id, dedupe_key, band, window, message_version.
- `alert_deliveries`: user, channel, status, provider_ref, error, timestamps.
- `alert_feedback`: delivery_id, rating, reason, created_at.
- `notification_preferences`: user, channel, target opt-ins, quiet hours, language.

---

## 10. Edge cases

| Case | Behaviour |
|---|---|
| Forecast downgraded after alert sent | No retraction message; next window reflects new band |
| Advisory expires mid-window | New alerts blocked; existing delivery unaffected; ops notified |
| Provider outage | Queue with backoff; mark `failed`; do not mark `sent` |
| Duplicate phone numbers | One delivery per user; dedupe at recipient level |
| User opted out | `suppressed`/`opted_out`; never resend unless re-opted |
| Area split/merged | New dedupe keys; historical alerts retain old code |
| Demo forecast | Excluded from operational alerts; demo badge if ever shown |
| Content validator false positive | Manual review path; cannot bypass without approver + audit |
| Emergency withdrawal | Immediate unpublish; all queued alerts for that advisory cancelled |
| Low coverage | No alert, regardless of band |

---

## 11. Non-functional requirements

| Area | Requirement |
|---|---|
| Latency | Alert dispatch within a configured window after forecast issue |
| Throughput | Batch dispatch supports pilot user count without provider throttling |
| Reliability | At-least-once delivery with idempotent provider refs; duplicates prevented at dedupe |
| Audit | Every approval, publish, withdrawal, send and suppression recorded |
| Privacy | Message contains no precise location or PII beyond the recipient's number |
| Localisation | Approved translations only; no machine translation of advisory text |
| Accessibility | SMS plain text; no reliance on emoji or colour |

---

## 12. Acceptance criteria

- [ ] Validator rejects each prohibited pattern class with a test.
- [ ] Advisory cannot be published without a second approver.
- [ ] Expired advisory is not returned by the API (test).
- [ ] Missing advisory returns fallback + escalation, never generated text.
- [ ] Alert is not sent when coverage is below threshold (test).
- [ ] Alert is not sent when the forecast is stale (test).
- [ ] Duplicate forecast run does not resend the same alert (test).
- [ ] Cooldown suppresses delivery and records `suppressed`.
- [ ] Message contains all required fields and the "not confirmation" sentence.
- [ ] Opt-out is honoured immediately for the next dispatch.
- [ ] Provider failure is retried and recorded, never marked delivered.
- [ ] Pausing alerts for an area stops dispatch within one job cycle.
- [ ] Feedback is stored and reportable by area/target/band.

---

## 13. Out of scope

- Chemical recommendations of any kind.
- Two-way conversational advisory.
- Personalised treatment plans.
- Voice/IVR in v1 (unless the partner mandates it).
- In-app purchases or input-dealer referrals.
- Automated content translation.

---

## 14. Open questions

1. Which SMS gateway (if any) does the partner operate? WhatsApp is out of v1 (D15).
2. Which named people hold `can_approve_advisory`, and are two of them available within the
   pilot's turnaround time?
3. What are the legal review requirements and turnaround for advisory content?
4. Is IVR required for low-literacy users in the pilot area? (Deferred unless mandated.)
5. What cooldown values are operationally acceptable without hiding a genuine escalation?

---

## 15. Blueprint traceability

| Blueprint chapter | Where this spec uses it |
|---|---|
| 38 — Combining image and forecast outputs | §5 alerts are generated from forecasts, not raw reports |
| 40 — Preventive advisory engine | §2 content model, §3 approval, §4 retrieval |
| 41 — Alert and notification design | §5 policy, §6 channels, §7 delivery |
| 44 — Privacy and responsible AI | §11 non-functional requirements |
| App. A — Sample farmer-facing alert | §6 template |
| App. E — API and integration checklist | §6 channels |

The no-chemical rule is a hard stop in `../docs-context/AGENTS.md` R5 and §8. The validator
is code with tests, not a style guide; see `../docs-context/ai-workflow-rules.md` §5.

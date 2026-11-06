# 02 — Reporting and capture

**Status:** Draft
**Owner:** Mobile lead (TBD)
**Depends on:** `01-design-system.md`, `03-auth-and-roles.md`, `05-data-layer.md`
**Implements:** farmer/field-staff report creation, quality feedback, offline queue, result
presentation, case history.

---

## 1. Goal

Let a field user record a crop observation with one photo and minimal typing, in poor
connectivity, and receive an honest photo assessment plus a clearly separate area outlook.

Success is not "the model answered". Success is: the report is captured, safely queued,
synced exactly once, and the user understands what the system can and cannot infer.

---

## 2. Users and stories

| ID | Story | Acceptance summary |
|---|---|---|
| US-02-01 | As a farmer, I select my crop and approximate field so the report has context | Context saved; unknown variety/stage allowed |
| US-02-02 | As a farmer, I capture a photo and am told if it is usable | Quality feedback within 3 s locally; retake offered |
| US-02-03 | As a farmer, I can save a report with no network | Report persisted locally; visible queued state |
| US-02-04 | As a farmer, I see the photo assessment and area outlook as separate cards | Distinct titles, timestamps, model versions |
| US-02-05 | As a farmer, I understand when the system cannot assess my photo | Neutral abstention state with reason and next step |
| US-02-06 | As a farmer, I can request expert review | Review request recorded and visible in history |
| US-02-07 | As a farmer, I can see the status and reviewer response for my cases | History shows sync + verification state |
| US-02-08 | As an extension worker, I can capture on behalf of a farmer | Optional farmer reference; same flow |

---

## 3. Flow

### 3.1 Online

```
Home
 └─ New report
     ├─ 1. Crop & context   (crop*, variety?, stage?, area*, notes?)
     ├─ 2. Capture          (camera | gallery, guidance, retake)
     ├─ 3. Local quality    (on-device pre-check: blur/exposure/resolution/plant)
     ├─ 4. Submit           (create observation → signed upload → complete)
     ├─ 5. Assessment       (server quality gate → classifier | abstain)
     └─ 6. Result           (AssessmentCard + OutlookCard, separate)
```

`*` required. Unknown variety/stage is explicitly selectable.

### 3.2 Offline

```
... steps 1–3 identical (all local)
 └─ 4. Save locally (status=queued, client_report_id generated)
     └─ Sync worker (connectivity regained)
         ├─ POST /observations (Idempotency-Key=client_report_id)
         ├─ signed upload → PUT → complete
         ├─ poll/fetch assessment
         └─ reconcile local row (server status wins; local history retained)
```

### 3.3 Queue state machine

```
draft ──save──► queued ──sync start──► uploading ──complete──► uploaded
                  ▲                        │                      │
                  │                        ▼                      ▼
                  └──── retry ◄──────── failed ◄─── error    assessed | abstained
                                                                    │
                                                                    ▼
                                                                 reviewed
```

Rules:

- `failed` is retryable and never deletes the report.
- `uploaded` is terminal for the upload step even if assessment is pending.
- `reviewed` is server-owned and read-only on device.
- The client may not transition to `assessed`; only the server can.
- A report may be deleted locally only if it was never queued, or the user explicitly
  discards a `failed` draft after a warning.

---

## 4. Functional requirements

### Context

| ID | Requirement | Priority |
|---|---|---|
| FR-02-01 | Select or search any crop from the open catalogue; the UI shows whether a photo assessment is available for it, and a crop without a validated target is still submittable but returns an explicit abstention | MUST |
| FR-02-02 | Select an approximate growing area from saved areas or admin units; no free-text precise coordinates required | MUST |
| FR-02-03 | Variety, growth stage and notes are optional; "unknown" is a first-class choice | MUST |
| FR-02-04 | Remember the last-used crop/area per device, but require confirmation before submit | SHOULD |

### Capture

| ID | Requirement | Priority |
|---|---|---|
| FR-02-05 | Capture with rear camera or choose from gallery | MUST |
| FR-02-06 | Show framing/lighting guidance before and during capture | MUST |
| FR-02-07 | Run an on-device pre-check for blur, exposure, resolution and plant presence | MUST |
| FR-02-08 | Allow retake without losing context; keep the best attempt by default | MUST |
| FR-02-09 | Record original dimensions, file size, capture source and pre-check result | MUST |
| FR-02-10 | Compress for upload while retaining diagnostic detail; record compression settings | MUST |

### Quality gate

| ID | Requirement | Priority |
|---|---|---|
| FR-02-11 | Server quality gate returns `pass` or a specific failure reason | MUST |
| FR-02-12 | Assessment runs only after `pass`; failure returns `abstained` with reason | MUST |
| FR-02-13 | Quality failure never prevents saving/submitting the report | MUST |
| FR-02-14 | User can retake and attach a new image to the same observation | MUST |
| FR-02-15 | Gate thresholds are configuration, versioned and recorded per prediction | MUST |

### Submission and sync

| ID | Requirement | Priority |
|---|---|---|
| FR-02-16 | Observation exists before image upload; failed upload does not lose the case | MUST |
| FR-02-17 | Client-generated `client_report_id` + `Idempotency-Key` prevents duplicates | MUST |
| FR-02-18 | Retry with backoff; expose retry count and last error | MUST |
| FR-02-19 | Upload resumes or restarts safely after interruption | MUST |
| FR-02-20 | Show queued/syncing/synced/failed distinctly, including queued count on Home | MUST |
| FR-02-21 | "Send on Wi-Fi only" preference respected | SHOULD |
| FR-02-22 | Warn before exceeding a configured local queue size; never silently drop | MUST |

### Result

| ID | Requirement | Priority |
|---|---|---|
| FR-02-23 | Render `AssessmentCard` and `OutlookCard` as separate components with distinct titles | MUST |
| FR-02-24 | Assessment shows up to 3 candidates, qualitative confidence, quality flags, model version, generated time | MUST |
| FR-02-25 | Abstention shows reason + retake + escalation; no candidate list | MUST |
| FR-02-26 | Unsupported crop shows supported list + escalation; never a forced class | MUST |
| FR-02-27 | Outlook shows band, horizon, drivers, coverage, issue/validity, model version, stale state | MUST |
| FR-02-28 | Result includes "not a diagnosis" and "low risk ≠ disease-free" wording | MUST |
| FR-02-29 | User can request expert review from the result | MUST |

### History

| ID | Requirement | Priority |
|---|---|---|
| FR-02-30 | List cases with date, crop, sync state, verification state, thumbnail | MUST |
| FR-02-31 | Case detail shows original image, assessment, outlook at time of report, review outcome | MUST |
| FR-02-32 | Reviewer response and corrected label are visible in plain language | MUST |
| FR-02-33 | Offline history reads from local cache; stale indicator where applicable | MUST |

---

## 5. API touchpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v1/config/crops` | Open crop catalogue + per-crop support status and target lists (cacheable) |
| `GET` | `/v1/areas` | Saved/available approximate areas |
| `POST` | `/v1/observations` | Create case (idempotent) |
| `POST` | `/v1/observations/{id}/images/upload-url` | Signed upload descriptor |
| `POST` | `/v1/observations/{id}/images/{image_id}/complete` | Finalise upload, trigger gate |
| `GET` | `/v1/observations/{id}` | Case + current states |
| `GET` | `/v1/observations/{id}/assessment` | Photo assessment result |
| `POST` | `/v1/observations/{id}/review-request` | Escalate |
| `GET` | `/v1/observations?cursor=` | History |

### Create observation (request)

```json
{
  "client_report_id": "0f0c2f8e-6a0f-4b1e-9d7a-3c9f0d2a1b44",
  "crop_code": "DEMO_CROP_01",
  "area_code": "DEMO_BLOCK_01",
  "variety": null,
  "growth_stage": "vegetative",
  "notes": null,
  "captured_at": "2026-11-06T09:10:00Z",
  "consent_version": "consent-2026-11"
}
```

Response: `201` with server `id`, `status: "pending_upload"`, `client_report_id` echoed.
A repeated `Idempotency-Key` returns `200` with the existing record.

### Assessment response (illustrative, demo values)

```json
{
  "observation_id": "obs_demo_001",
  "state": "assessed",
  "quality": {"result": "pass", "flags": []},
  "candidates": [
    {"label": "late_blight", "band": "medium"},
    {"label": "early_blight", "band": "low"},
    {"label": "nutrient_deficiency", "band": "low"}
  ],
  "confidence": {"band": "medium", "calibrated": true},
  "model_version": "photo-demo-0.3.1",
  "generated_at": "2026-11-06T09:14:00Z",
  "is_demo": true
}
```

`is_demo` is mandatory for seeded/demo records and must render a visible demo badge.

### Abstention response (illustrative)

```json
{
  "observation_id": "obs_demo_002",
  "state": "abstained",
  "abstention_reason": "unsupported_target",
  "quality": {"result": "pass", "flags": []},
  "candidates": [],
  "model_version": "photo-demo-0.3.1",
  "generated_at": "2026-11-06T09:14:00Z",
  "is_demo": true
}
```

The abstention vocabulary is fixed by ADR-011: `unsupported_crop`, `unsupported_target`,
`insufficient_quality`. An abstention is never rendered as a negative result, a healthy
plant or "no disease".

---

## 6. Data model touchpoints

- `observations`: id, client_report_id (unique per user), user_id, crop_code, area_code,
  variety, growth_stage, notes, captured_at, submitted_at, sync/assessment state.
- `image_assets`: observation_id, storage_key, original dims, bytes, content hash,
  compression config, source (camera/gallery), upload state.
- `image_quality_results`: image_id, gate_version, result, flags, thresholds snapshot.
- `image_predictions`: image_id, model_version, candidates JSON, confidence band,
  calibration status, abstained flag, generated_at. Insert-only.
- `review_requests`: observation_id, requested_by, reason, created_at.
- `audit_events`: creation, upload complete, review request.

---

## 7. Edge cases

| Case | Required behaviour |
|---|---|
| Camera permission denied | Explain, offer gallery, link to settings |
| Storage full | Block capture with clear message; preserve existing queue |
| App killed mid-upload | On restart, resume from `uploading`; verify with server |
| Duplicate retry | Same idempotency key returns existing case |
| Server rejects image type/size | Mark image `failed`, keep observation, explain |
| Crop removed from supported list mid-flight | Keep case; assessment returns `unsupported_crop` |
| Area no longer valid | Keep case; outlook returns `insufficient_data` with reason |
| Clock skew | Use server time for display ordering; keep device `captured_at` as metadata |
| Image already assessed, user retakes | New image asset + new prediction; old prediction retained |
| User has 50+ queued reports | Batch sync with rate limiting; show progress |
| App update with queued rows | Migration preserves queue; test with populated DB |
| Account deleted while queue non-empty | Warn; require explicit discard or sync first |

---

## 8. Non-functional requirements

| Area | Requirement |
|---|---|
| Capture responsiveness | Local UI response < 100 ms; pre-check < 3 s on target device |
| Upload | Resumable/retryable; compression recorded; no duplicate bytes on retry |
| Offline | Full context + capture + queue works with no network for ≥ 7 days of typical use |
| Storage | Queue capped by config; warn at 80%; never silent eviction |
| Battery | No background GPS; sync batched; no wake-lock during idle |
| Accessibility | All states reachable by screen reader; 48 dp targets; font scaling to 200% |
| Localisation | All strings externalised in i18n catalogues; English + Kannada |
| Security | Images stored privately in Cloudinary; signed URLs short-lived; no EXIF location leak without consent |
| Privacy | Approximate area only; no precise coordinates required to submit |

---

## 9. Acceptance criteria

- [ ] A supported crop report can be created online and returns a case reference.
- [ ] A blurry image returns `abstained` with `blurry` and a retake action; no candidates shown.
- [ ] An unsupported crop never produces a class; it returns `unsupported_crop` and the
      catalogue shows the support status.
- [ ] Airplane mode: report saves, shows queued, syncs on reconnect.
- [ ] Retrying a failed upload does not create a second observation.
- [ ] Killing the app mid-upload does not lose the report.
- [ ] Result screen shows two separate cards with distinct titles and timestamps.
- [ ] Outlook `insufficient_data` renders when the weather snapshot is stale.
- [ ] Expired cached outlook is marked stale, including while offline.
- [ ] History shows sync and verification states, and the reviewer response.
- [ ] Queue size warning appears at the configured threshold.
- [ ] Every new string is in the i18n catalogues; no hard-coded copy.
- [ ] Component and E2E tests cover: result, abstained, unsupported, stale, queued, failed.

---

## 10. Telemetry and audit

Events: `observation.created`, `image.uploaded`, `quality.evaluated`,
`assessment.generated`, `assessment.abstained`, `review.requested`, `sync.retried`,
`sync.failed`, `queue.threshold_warned`.

Never log image bytes, notes, phone numbers or coordinates. Include `request_id`,
`observation_id`, `model_version`, `gate_version`, duration and outcome.

---

## 11. Out of scope

- Multi-image diagnosis per case (v1 assesses one image at a time).
- ~~Video capture.~~ **Superseded by `09-video-reading.md` (explicit user instruction,
  2026-11-06).** Video is a capture format over the same photo-assessment pipeline; it
  never produces a video-level diagnosis, severity, yield loss or area outlook.
- On-device model inference. (The FR-02-07 pre-check is client-side and advisory only; its
  mechanism is decided in `progress-tracker.md` D12. The server quality gate is
  authoritative.)
- Farmer-to-farmer sharing.
- Yield or loss estimation.
- Precise GPS field mapping.

---

## 12. Open questions

1. Does the pilot partner require reports to be created on behalf of a farmer (worker
   identity vs farmer identity)? Affects `user_id` semantics. (D11)
2. What is the maximum acceptable image size on the partner's data plan?
3. Is an SMS gateway available for outlook alerts, or is in-app the only v1 channel? (D15)
4. Should a report allow a symptom questionnaire (leaf position, spread pattern) in v1?
   It improves triage but adds friction.

---

## 13. Blueprint traceability

| Blueprint chapter | Where this spec uses it |
|---|---|
| 15 — Farmer mobile application design | §3 flow, §4 requirements, §8 |
| 19 — Image dataset collection | Capture protocol and metadata in §4, §6 |
| 27 — Image diagnosis problem formulation | §3.3 assessment states, §4 result requirements |
| 42 — Offline-first engineering | §3.2, §4 submission/sync, §7 edge cases |
| App. B — Sample image assessment wording | §5 assessment response, `ui-context.md` §2 |

Data rules for capture metadata, compression and provenance are in
`../docs-context/data-foundation.md` §3. Offline state rules are in
`../docs-context/ai-workflow-rules.md` §6.

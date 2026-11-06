# 09 — Video reading (AI video-reading system)

**Status:** Draft — accepted for a demo-labelled machinery slice on 2026-11-06 by
explicit user instruction. Video was previously listed as out of scope in
`02-reporting-and-capture.md` §11 and `08-conversational-capture.md` §3.2; this
spec supersedes those two exclusions for the scope described here.
**Owner:** Product lead + ML lead
**Depends on:** `02-reporting-and-capture.md`, `03-auth-and-roles.md`,
`04-expert-review.md`, `05-data-layer.md`, `08-conversational-capture.md`,
`../docs-context/ml-models.md`
**Implements:** a short-clip capture path where a user records or uploads a video
of a plant and receives per-frame photo assessments plus a **non-diagnostic**
video summary.

---

## 1. Goal

Extend the photo-assessment pipeline from one image to a short clip without
turning video into a new diagnostic output.

A video is **not** a new model and **not** a new "risk" number. It is a capture
format that produces:

1. a bounded set of sampled frames, each run through the existing image quality
   gate and assessment engine;
2. a tracked-region summary describing what moved/stayed stable across frames;
3. a video-level summary that reports **visibility, quality and consistency**,
   never a single diagnosis and never area outlook.

The user still sees the same safety contract as chat: candidates are unverified,
abstention is a valid result, expert review is one action away, and no chemical
advice is ever produced.

---

## 2. Why this needs its own spec

The three pipeline stages have different failure modes from a still image:

| Stage | Risk if done carelessly |
|---|---|
| Frame extraction | Sampling one lucky frame and presenting it as "the video"; unbounded decode cost; accepting corrupt/oversized files. |
| Object tracking | Presenting a tracker id as an identified pest; a tracker needs a detector, and a detector needs a validated model and taxonomy. |
| Video-level summary | Collapsing many frames into one confident label — a diagnosis by aggregation. |

Therefore the machinery ships **before** any real detector model, visibly
labelled, and the model seam is explicit.

---

## 3. Scope

### 3.1 In scope

- Short clips (bounded duration and size) uploaded from the web/mobile chat
  composer.
- Server-side decode and bounded frame sampling.
- Per-frame quality gate using the existing `demo-quality-0.1` metrics.
- A pluggable detector seam. The default implementation is a deterministic
  **motion-region** detector (`demo-motion-0.1`), explicitly not a pest detector.
- A pluggable tracker seam. The default implementation is a versioned,
  dependency-light two-stage IoU tracker (`bytetrack-lite-0.1`), documented as a
  reimplementation, not the official ByteTrack package.
- Per-frame assessment through the existing `AssessmentEngine` for the best
  usable frames.
- A template-rendered video summary with explicit abstention reasons.
- Persisted video metadata and append-only readings.
- A preview of the first sampled frame.

### 3.2 Out of scope

- Live/streaming video, RTSP, drone feeds.
- Multi-object pest identification, species recognition, counting pests.
- A trained detector or a trained video model of any kind.
- Video-level classification, severity scoring or yield loss.
- Area outlook from video.
- Audio, voice, or transcript processing.
- Retaining video indefinitely; retention is decision D14 (open).
- Mobile capture UI in this slice (backend + web follow).

---

## 4. Flow

```
record / choose clip
  → POST /v1/videos                     (validate type, size, duration, decode)
  → POST /v1/videos/{id}/read           (sample → quality → detect → track → assess)
       ├─ assessed    → per-frame cards + non-diagnostic summary + review action
       ├─ abstained   → reason (no usable frames, no stable region, too short)
       └─ failed      → decode/engine failure, no invented result
  → GET /v1/videos/{id}                 (metadata + latest reading)
  → GET /v1/videos/{id}/preview         (first sampled frame, owner-scoped)
```

Reading is append-only: a re-read creates a new reading row, so a later model or
threshold change never rewrites history.

---

## 5. Requirements

| ID | Priority | Requirement |
|---|---|---|
| VID-01 | Must | Accept MP4/MOV/WebM clips only, verify the container decodes, enforce a byte ceiling, a duration ceiling and a resolution ceiling. Reject anything else with a stable error code. |
| VID-02 | Must | Sample frames on a bounded schedule (`video_sample_fps`, `video_max_frames`) and downscale each frame to a bounded side. Sampling must be deterministic for the same file and settings. |
| VID-03 | Must | Run every sampled frame through the existing image quality gate and persist the result and flags per frame. |
| VID-04 | Must | Provide a detector seam. The default `demo-motion-0.1` detector returns motion regions from frame differencing and must be labelled demo; it must never be described as a pest detector. |
| VID-05 | Must | Provide a tracker seam. `bytetrack-lite-0.1` associates high-score then low-score detections by IoU and keeps stable ids across frames. It is a reimplementation, not the official ByteTrack library. |
| VID-06 | Must | Run the configured `AssessmentEngine` on at most `video_assess_frames` best usable frames. Record the engine version and `is_demo` per frame. |
| VID-07 | Must | Produce a video summary from fixed templates: sampled/usable frame counts, quality distribution, tracked-region count and duration, and candidates observed with their frame counts. Never a single video-level diagnosis. |
| VID-08 | Must | Abstain with a reason when there are too few usable frames, no stable region, or the clip is too short. Abstention returns no video-level candidates. |
| VID-09 | Must | Fail closed on decode errors, engine failures and unsafe summary text (`unsafe_content_blocked`); never fabricate a result. |
| VID-10 | Must | Persist the video metadata and each reading (versions, timestamps, `is_demo`, `calibrated=false`) append-only. |
| VID-11 | Must | Serve the stored video and preview only through owner-scoped routes; no public URL, no directory listing. |
| VID-12 | Must | Never emit chemical products, doses, mixtures, intervals or spray instructions. Summary text and candidate display names pass `chat-safety-0.1`. |
| VID-13 | Must | Mark every summary `requires_review=true`; video output never auto-verifies a case and never enters forecast features. |
| VID-14 | Should | Expose a stable preview (first sampled frame as JPEG) so the client can show what was read. |
| VID-15 | Later | Replace `demo-motion-0.1` with a validated detector behind the same seam (needs D1/D2, a labelled dataset, calibration and the D8 decision function). |
| VID-16 | Later | Chat-composer integration on web and mobile, including the video card and review action. |

---

## 6. States and reason codes

| State | Meaning |
|---|---|
| `assessed` | At least one usable frame was assessed and at least one region was tracked. |
| `abstained` | The clip cannot support an assessment. `reason_code` is one of `insufficient_usable_frames`, `no_stable_region`, `clip_too_short`, `no_frames`. |
| `failed` | Decode, storage or engine failure. `error_code` is one of `video_decode_failed`, `video_not_found`, `model_not_configured`, `model_unavailable`, `model_timeout`, `invalid_model_response`, `unsafe_content_blocked`. |

`confidence_band` is always `not_calibrated` and `calibrated` is always `false`
until a validated model and calibration exist.

---

## 7. API contract

```
POST /v1/videos                        # multipart; returns VideoDescriptor (201)
GET  /v1/videos/{video_id}             # metadata + latest reading, if any
GET  /v1/videos/{video_id}/preview     # first sampled frame (image/jpeg)
POST /v1/videos/{video_id}/read        # run the pipeline; returns VideoReading (201)
```

`VideoReading` fields:

```json
{
  "reading_id": "vidr_...",
  "video_id": "vid_...",
  "state": "assessed",
  "reason_code": null,
  "error_code": null,
  "summary_text": "Video summary: ...",
  "sampled_frames": 12,
  "usable_frames": 9,
  "duration_ms": 4200,
  "quality": {"pass": 9, "blurry": 3},
  "tracks": [{"track_id": 1, "frames": 6, "duration_ms": 1500, "mean_area_fraction": 0.07}],
  "candidates_observed": [{"label": "...", "display_name": "...", "frames": 2}],
  "frames": [
    {
      "index": 4,
      "timestamp_ms": 800,
      "quality_result": "pass",
      "quality_flags": [],
      "track_ids": [1],
      "assessment": {"state": "assessed", "candidates": [], "model_version": "..."}
    }
  ],
  "engine_version": "demo-chat-0.1",
  "detector_version": "demo-motion-0.1",
  "tracker_version": "bytetrack-lite-0.1",
  "is_demo": true,
  "calibrated": false,
  "confidence_band": "not_calibrated",
  "requires_review": true,
  "generated_at": "2026-11-06T00:00:00Z"
}
```

Rules:

- `frames` contains only sampled frames that were assessed, capped by
  `video_assess_frames`; it is not the full frame dump.
- `candidates_observed` counts frames in which a candidate appeared. It is not a
  probability and must not be rendered as one.
- `tracks` describes motion regions, not pests.
- The video bytes stay outside the database; only metadata and the relative
  storage path are persisted.

---

## 8. Data model

Two additive tables in Alembic `0003_video_persistence`:

- `video_uploads` — owner, filename, content type, size, SHA-256, storage path,
  duration, width, height, fps, frame count, created/deleted timestamps.
- `video_readings` — append-only: video id, owner, state, reason/error code,
  summary JSON, frames JSON, engine/detector/tracker versions, `is_demo`,
  `calibrated`, `generated_at`.

Rollback note: `downgrade()` drops `video_readings` then `video_uploads`; the
`0002_chat_persistence` tables are untouched.

---

## 9. Safety and privacy

- **R1:** the summary is a photo-assessment aggregate, never an area outlook.
- **R2:** abstention is a first-class result; no nearest-class fallback.
- **R4:** `requires_review=true` on every reading; nothing is auto-verified.
- **R5:** fixed templates only; `chat-safety-0.1` runs on the summary and
  candidate display names before storage.
- **R6:** `demo-motion-0.1`, `bytetrack-lite-0.1` and the demo engine are named
  and labelled; no performance metric is claimed.
- **R7:** engine/detector/tracker versions, timestamps and frame snapshots are
  recorded; readings are append-only.
- **R9:** owner-scoped access, no public URL, no exact location from video.
  Faces/background people are not analysed. Retention is D14 (open); the slice
  stores the source clip so a reading can be reproduced and soft-deletes only
  when a retention job exists.
- **R10:** this spec and the progress tracker are updated with the code.

---

## 10. Acceptance criteria

- [ ] A synthetic clip uploads, samples deterministically, tracks a moving
      region with a stable id, and returns `assessed` with per-frame assessments.
- [ ] A clip with too few usable frames returns `abstained` /
      `insufficient_usable_frames` and no video-level candidates.
- [ ] A corrupt or unsupported file is rejected without a stored row.
- [ ] An engine returning unsafe text is stored as `failed` /
      `unsafe_content_blocked`.
- [ ] Readings are append-only and expose versions, `is_demo` and
      `requires_review`.
- [ ] Preview is owner-scoped and byte-identical to the first sampled frame.
- [ ] Full backend suite and targeted lint pass; `alembic upgrade head --sql`
      emits the new revision.

---

## 11. Open decisions

| ID | Question | Owner | Blocks |
|---|---|---|---|
| D1/D2 | Crop and target taxonomy | Product + agronomist | A real detector and any real label set |
| D8 | Abstention/operating point | ML lead | Calling any video output calibrated |
| D14 | Video retention and deletion window | Product + privacy | Hard delete, object-storage lifecycle |
| D15 | Detector/tracker model and validation protocol | ML lead | Replacing `demo-motion-0.1` |

Until D15 is decided and a validated artefact exists, `demo-motion-0.1` and
`bytetrack-lite-0.1` are the only shipped implementations and every reading is
demo-labelled.

# 08 — Conversational capture (chat)

**Status:** Draft
**Owner:** Product lead + frontend lead
**Depends on:** `02-reporting-and-capture.md`, `03-auth-and-roles.md`,
`04-expert-review.md`, `05-data-layer.md`, `06-forecast-and-risk-map.md`,
`07-advisory-and-alerts.md`
**Implements:** the chat surface used on **web and mobile**, where a user attaches or
takes an image, adds optional context, sends it, and receives an AI photo-assessment
reply.

---

## 1. Goal

Give farmers and field staff one obvious entry point: **a chat where they can show the
plant**. The chat is a *conversation wrapper* around the existing photo-assessment
pipeline; it is not a new model and it is not a free-form diagnosis bot.

The reply is a **structured assessment card**:

- what the model thinks it may be seeing (top candidates, confidence band);
- an explicit abstention with a reason and a retake action when quality fails;
- the next safe step (retake, add context, request expert review, read approved
  advisory);
- the model version and generation timestamp.

**What the chat must never do**

- Never present a candidate as a diagnosis or confirmed outbreak.
- Never merge photo assessment with area outlook in one reply or number.
- Never produce chemical names, doses, mixtures, intervals or legal-use advice.
- Never answer "is this disease X?" with an unsupported guess; it abstains.
- Never invent a result when the backend is unreachable; it shows a queued state.

This spec adds the surface and its contracts. It does not change the model, the
verification model or the risk semantics.

---

## 2. Users and jobs

| User | Job | Surface |
|---|---|---|
| Farmer | "Something is wrong with this plant — what might it be, and what can I do safely?" | Mobile chat, web chat |
| Field staff / extension worker | Capture evidence quickly, add context, route to expert review | Mobile chat |
| Expert (agronomist / senior extension worker) | See the conversation and image that produced a case, without a second tool | Web chat + expert portal |
| Admin | Audit conversations and message events; never browse content without a reason | Admin console |

All users are authenticated. A conversation is private to its owner; staff access is
role- and area-scoped and audited.

---

## 3. Scope

### 3.1 In scope

- A chat thread list and a message thread on **mobile (React Native + TypeScript)** and
  **web (Next.js)**.
- Sending an image from camera or gallery through the chat composer.
- Optional short text context (`crop`, `growth stage`, `area`, symptom note); unknown is
  allowed.
- Server-side photo assessment triggered by the message; structured reply card.
- Abstention, unsupported-crop, queued/offline, failed and review-requested states.
- Request expert review from inside the conversation.
- Deep link from the chat reply to the separate area-outlook card.
- Conversation history, read state, delete conversation (privacy flow).
- Offline queue for mobile; the same contract works online on web.

### 3.2 Out of scope

- Free-form generative diagnosis or treatment conversation.
- A general-purpose chatbot for non crop-health topics.
- Voice messages and live streaming. ~~Video.~~ **Video is superseded by
  `09-video-reading.md` (explicit user instruction, 2026-11-06):** a clip is read as
  sampled frames with per-frame photo assessments and a non-diagnostic summary, never a
  video-level diagnosis.
- Multi-user group chats.
- Automatic translation of user text.
- Merging area outlook into the chat reply.
- Model training on chat text.

---

## 4. Flow

```
open chat
  → attach image (camera/gallery) or drag-and-drop (web)
  → optional context: crop, stage, approximate area, short note
  → send
       ├─ online:  create message → upload image → quality gate → assessment
       └─ offline: queue locally → send on reconnect (same idempotency key)
  → assistant reply (structured, one of):
       ├─ assessed      → candidate card + confidence + next safe step
       ├─ abstained     → reason + retake action (image kept)
       ├─ unsupported   → catalogue support status + escalation (never a forced class)
       ├─ queued        → "will assess when connected"
       ├─ failed        → retry action, no invented result
       └─ review        → request created, status visible
  → user can: retake, add context, request expert review, open advisory,
    open the separate area-outlook card
```

A retake is a **new message** in the same thread linked to the same observation. The
previous image is retained; history is append-only from the user's perspective.

---

## 5. Functional requirements

| ID | Priority | Requirement |
|---|---|---|
| CHAT-01 | Must | A signed-in user can open a conversation list and a conversation thread on web and mobile. |
| CHAT-02 | Must | The composer accepts an image from camera or gallery (web: file picker/drag-drop) plus optional short text. |
| CHAT-03 | Must | Sending an image creates exactly one observation and one user message, linked by `client_message_id`; retries do not duplicate either. |
| CHAT-04 | Must | While offline, the message is stored locally and shown as `queued`; it is sent on reconnect with the same idempotency key. |
| CHAT-05 | Must | The assistant reply is rendered as an `AssessmentCard`, never as free-form prose containing a diagnosis. |
| CHAT-06 | Must | The card shows top candidates, confidence band (or `not_calibrated`), `model_version`, `generated_at` and calibration status. |
| CHAT-07 | Must | If the quality gate or domain check fails, the reply is `abstained` with a D8 machine reason (`below_class_threshold`, `low_margin`, `high_entropy`, `out_of_distribution`, `unsupported_crop`, `quality_gate_failed` plus the quality flag), a plain-language explanation and a retake action. |
| CHAT-08 | Must | If the crop is unsupported, the reply explains this, lists supported crops and offers escalation; no class is forced. |
| CHAT-09 | Must | The user can request expert review from the reply; the request is created against the observation and is visible in the thread. |
| CHAT-10 | Must | The reply must never contain a chemical name, dose, mixture, interval or legal-use instruction. A server-side validator blocks unsafe content. |
| CHAT-11 | Must | Photo assessment and area outlook remain visually separate: the chat may link to an outlook card, but never merges it into the assessment reply. |
| CHAT-12 | Must | Conversation content is private to the owner; staff access is role-scoped, audited and reason-recorded. |
| CHAT-13 | Must | Every assistant reply is persisted with its assessment reference, template/model version and timestamp; history is not reconstructed from today's data. |
| CHAT-14 | Must | A failed upload or assessment shows a retry action and never a fabricated result. |
| CHAT-15 | Should | Conversation list shows crop/area context, last message preview and unread state. |
| CHAT-16 | Should | The user can delete a conversation; the privacy deletion flow covers messages and attachments. |
| CHAT-17 | Should | Cached conversations and replies render with a stale marker after their validity window. |
| CHAT-18 | Must | No chat control changes a model output; an abstained reply stays abstained, retake creates a new assessment, and review is a separate audited request (D8). |
| CHAT-18 | Should | The composer is usable with one hand on a low-end Android device and with a keyboard/screen reader on web. |
| CHAT-19 | Later | An approved LLM may rephrase approved template content only; it must pass the same validator and never add facts. |

---

## 6. Reply contract

### 6.1 Assessed

```json
{
  "message_id": "msg_demo_002",
  "role": "assistant",
  "kind": "assessment",
  "observation_id": "obs_demo_001",
  "assessment": {
    "state": "assessed",
    "candidates": [
      {"label": "late_blight", "band": "medium"},
      {"label": "abiotic_lookalike", "band": "low"},
      {"label": "unknown", "band": "low"}
    ],
    "confidence_band": "medium",
    "calibrated": false,
    "probability": null,
    "quality_flags": [],
    "model_version": "image-classifier-demo-0.1",
    "generated_at": "2026-11-06T06:00:00Z",
    "is_demo": true
  },
  "next_steps": ["add_context", "request_review", "read_advisory"],
  "created_at": "2026-11-06T06:00:01Z"
}
```

### 6.2 Abstained

```json
{
  "message_id": "msg_demo_003",
  "role": "assistant",
  "kind": "abstained",
  "observation_id": "obs_demo_002",
  "reason_code": "blur",
  "reason_text": "The image is too blurry to assess.",
  "next_steps": ["retake"],
  "model_version": "image-quality-gate-demo-0.1",
  "generated_at": "2026-11-06T06:00:00Z",
  "is_demo": true
}
```

### 6.3 Queued / failed / review

| Kind | Required fields | User action |
|---|---|---|
| `queued` | `client_message_id`, `queued_at` | wait, view queue |
| `failed` | `client_message_id`, `error_code`, `retryable` | retry, delete |
| `review_requested` | `review_request_id`, `status`, `submitted_at` | view status |
| `unsupported_crop` | `catalogue_link`, `reason_code` | change crop, escalate |

`is_demo` is mandatory for any synthetic or illustrative reply. It must render a demo
badge in every client.

---

## 7. API touchpoints

```
GET    /v1/conversations?cursor=
POST   /v1/conversations
GET    /v1/conversations/{id}
DELETE /v1/conversations/{id}
GET    /v1/conversations/{id}/messages?cursor=
POST   /v1/conversations/{id}/messages
POST   /v1/conversations/{id}/messages/{message_id}/retry
POST   /v1/conversations/{id}/messages/{message_id}/review
POST   /v1/uploads                              # multipart image upload (Phase 2 demo)
GET    /v1/uploads/{upload_id}                  # owner-scoped preview bytes
GET    /v1/conversations/{id}/events            # optional SSE; polling otherwise
```

`POST /v1/conversations/{id}/messages` accepts JSON. An image is uploaded first with a
multipart `POST /v1/uploads`; the message then references the returned `upload_id`:

```json
{
  "client_message_id": "cm_01H...",
  "text": "Leaves have brown spots",
  "observation_id": null,
  "image": {
    "upload_id": "up_01H...",
    "content_hash": "sha256:...",
    "content_type": "image/jpeg"
  }
}
```

Rules:

- `Idempotency-Key` is required, matching `client_message_id` semantics.
- The server validates and stores the image before the message is accepted. In the
  Phase 2 demo slice the `image_uploads` row is the observation record for the turn;
  creating a full `observations` row and linking `image_assets` is deferred until the
  capture pipeline in spec 02 lands.
- The server returns the stored user and assistant messages, each with its structured
  `assessment`/`image` descriptor; the client renders the card from those fields.
- No endpoint returns raw scores to farmer clients beyond the documented candidates.
- An assistant message is append-only. `POST …/review` creates at most one
  `chat_review_requests` row per assistant message and returns the same row on replay.
- Every assistant reply is validated before it is stored. If the reply text, the
  assessment reason or a candidate display name contains a chemical product, dose,
  mixture, application interval or spray instruction, the turn is stored as `failed`
  with `reason_code`/`error_code` `unsafe_content_blocked`, no candidates and
  `next_steps` set to `["request_review"]`. A `validator_rejected` `message_events` row
  records the validator version and rule categories; the unsafe text is never stored.
- The assessment engine is a pluggable seam. `APP_CHAT_ENGINE=demo` serves the
  deterministic labelled engine; `APP_CHAT_ENGINE=openai_compatible` calls a vision
  model through an OpenAI-compatible chat-completions endpoint. The model may only
  choose from the configured `APP_CHAT_LABELS`; the server renders the reply from fixed
  templates, so the provider never supplies user-facing advice. Missing key/model/labels
  and malformed output become `failed` states (`model_not_configured`,
  `invalid_model_response`, `model_unavailable`, `model_timeout`); a model abstention
  becomes `abstained`/`model_abstained`. `is_demo` stays true until the label set is the
  approved D1/D2 taxonomy and `APP_CHAT_LABELS_APPROVED=true`; no taxonomy is invented in
  code.

---

## 8. Data model touchpoints

| Table | Purpose | Key constraints |
|---|---|---|
| `conversations` | Thread owned by one user | `owner_id` (demo owner until auth); `deleted_at` for user deletion |
| `messages` | Append-only user and assistant messages | `conversation_id`; `client_message_id` unique per conversation; `turn_id` pairs the user/assistant rows |
| `message_events` | delivery/assessment/review state transitions | append-only |
| `image_uploads` | Validated image metadata and quality metrics | `owner_id`; SHA-256; bytes live outside the database |
| `chat_review_requests` | Expert-review request for one assistant message | unique `message_id`; separate from the observation-review `review_requests` table |

Replies store an immutable `assessment` JSON snapshot (`model_version`, `generated_at`,
`calibrated`, `is_demo`) and, for an image turn, an `image` JSON descriptor referencing
the `image_uploads` row. The `assistant` message is never edited; corrections are new
messages.

Phase 2 implements this demo path. Linking a message to `image_assets` through
`message_attachments` is deferred until the observation pipeline in spec 02 is wired in;
the upload row and the message descriptor are the traceable record in the meantime.

---

## 9. Safety and responsible AI

The chat is the most likely place for a user to read a model output as a diagnosis, so
the following are hard requirements:

1. The first line of an assessed reply says it is an **assistive photo assessment**, not
   a diagnosis.
2. A candidate is always accompanied by confidence and the abstention/uncertainty
   context.
3. The reply offers **no chemical treatment**. Action types are limited to scouting,
   monitoring, sanitation, crop management and escalation.
4. Severe, uncertain or unsupported cases surface "request expert review" as the primary
   action.
5. The server-side content validator (`chat-safety-0.1`) rejects chemical vocabulary
   before a message is stored. It is fail-closed: a blocked reply becomes a `failed`
   assessment with no candidates, and the rejection is audited without copying the
   unsafe text. Unit and API tests assert this.
6. No free-form generative text is served in v1. Template rendering is deterministic and
   versioned.
7. The chat cannot be used to bypass verification: requesting review creates the same
   review request and audit event as the non-chat capture flow.

---

## 10. Offline and failure behaviour

| Condition | Behaviour |
|---|---|
| Offline, image attached | Save locally, show `queued`, retain image and context |
| Upload interrupted | Resume or restart with the same key; no duplicate observation |
| Server unreachable | `queued`/`failed` with retry; never a fake reply |
| Quality gate fails | `abstained` + retake; image retained in history |
| Model unavailable | `failed` with retryable code; no stale guessed result |
| Cached conversation | Rendered with last-updated time and stale marker after validity |
| Deleted conversation | Removed from list; deletion completes per privacy flow |

### Implementation status (2026-11-06)

- **Web:** image upload, structured card and idempotent retry are implemented; the
  offline path is an in-page notice with manual retry, not a durable queue.
- **Mobile:** the slice above is implemented in `mobile/lib/src/outbox.dart`,
  `chat_sync.dart`, `api_client.dart` and `main.dart`. A turn is written to a
  persisted outbox (`ps03.chat.outbox.v1`) before the first network call, shown as
  `queued`, and flushed in order on manual retry, a 15-second page timer and app
  resume. The upload id and conversation id are persisted so a retry reuses them
  with the same `client_message_id`.
- **Failure honesty:** non-retryable errors and a missing local image become a
  visible `failed` turn with Retry/Delete; the client never renders a local
  placeholder as an assistant reply.
- **Verified:** `flutter analyze` clean and `flutter test` 14 passed. No device,
  emulator or airplane-mode run has been performed, so this row is unit evidence
  only until an APK exists.
- **Known deviation:** v1 uses the demo multipart `POST /v1/uploads` described in
  §6, not the presigned-URL flow in CHAT-NF-03. The signed-upload pipeline remains
  open for the pilot-scale implementation.
- **Known limit:** the picker's cache copy can be evicted by the OS before a
  reconnect; that is surfaced as a failed turn rather than hidden. There is no
  background worker or connectivity listener in this slice.

---

## 11. Non-functional requirements

| ID | Requirement |
|---|---|
| CHAT-NF-01 | Mobile chat remains usable on a low-end Android device and a constrained network. |
| CHAT-NF-02 | Web chat is keyboard operable, labelled, and meets the contrast/focus rules in `01-design-system.md`. |
| CHAT-NF-03 | Image upload uses the existing signed-upload pipeline; no multipart through the API process. |
| CHAT-NF-04 | Message and attachment access is authorised per conversation; IDs are unguessable (UUID). |
| CHAT-NF-05 | Logs include conversation/message identifiers and states, never image bytes, coordinates or user text. |
| CHAT-NF-06 | Reply templates are externalised for translation; no hard-coded user-facing copy. |
| CHAT-NF-07 | The composer and reply cards obey the same offline/stale/error state matrix as the rest of the app. |

---

## 12. Acceptance criteria

- [ ] A user can send an image from mobile and web and receives a structured reply card.
- [ ] Retrying the same send produces one observation and one message.
- [ ] Airplane-mode send is queued and delivered once after reconnect.
- [ ] A blurry image yields `abstained` with a retake action; the image stays in history.
- [ ] An unsupported crop yields the supported list; no class is forced.
- [ ] The reply shows model version, generation time and calibration status.
- [ ] The reply never contains chemical advice; the validator test fails the build if it does.
- [ ] Photo assessment and area outlook are never merged in a reply or card.
- [ ] Requesting review from chat creates the same review request and audit event as spec 04.
- [ ] Another user cannot read the conversation (403).
- [ ] Conversation deletion removes messages and attachments per the privacy flow.
- [ ] Demo replies are visibly badged `is_demo` in every client.
- [ ] Offline, failed and stale states all render with a next action; none shows a fake result.

---

## 13. Telemetry and audit

Metrics: messages sent, images attached, assessment replies by state (assessed,
abstained, unsupported, failed), median time to reply, retake rate, review requests from
chat, validator rejections, conversation deletion completions.

Audit events: conversation created/deleted, review requested, staff access with reason,
validator rejection, reply generated (with model and template versions).

No user text, image bytes or coordinates in logs.

---

## 14. Traceability

| Concern | Document |
|---|---|
| Capture, quality, offline queue | `02-reporting-and-capture.md` |
| Auth, roles, consent, privacy deletion | `03-auth-and-roles.md` |
| Review request and verification | `04-expert-review.md` |
| Tables, constraints, storage | `05-data-layer.md` |
| Separate area-outlook card | `06-forecast-and-risk-map.md` |
| Approved non-chemical advisory | `07-advisory-and-alerts.md` |
| Wording, tokens, states | `01-design-system.md`, `../docs-context/ui-context.md` |
| Rules R1–R10 | `../docs-context/AGENTS.md` |

---

## 15. Open questions

1. **Streaming vs polling** for the assistant reply: v1 uses a single request that returns
   when the assessment is ready, with polling fallback. Confirm at scaffold.
2. **Conversation retention period** is a programme/legal decision; the mechanism ships
   now.
3. **One image per message** in v1; multi-image messages are deferred.
4. **LLM rephrasing** is out of scope until the validator and evaluation suite exist.

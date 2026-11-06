# UI context

**Purpose:** the shared visual, verbal and interaction rules for the mobile app, web app,
expert portal and district dashboard, including the conversational capture surface.
**Rule of thumb:** a farmer should always be able to answer three questions — *what does
this mean, how sure is it, and what do I do next?*
**Last updated:** 2026-11-06

---

## 1. Design principles

1. **Separate before you simplify.** Photo assessment and area outlook are two cards,
   with different labels, timestamps and model versions. Simplification must not merge
   them.
2. **Uncertainty is content, not a disclaimer.** Show it in the card, in plain language,
   at the same visual weight as the result.
3. **Abstention is a valid outcome.** "No assessment" is designed, not an error state.
4. **Action before analysis.** Every screen ends with one clear next step or an explicit
   "nothing to do now".
5. **Offline is visible.** Queued, syncing, synced, stale and expired each have a distinct
   state. Never show cached data as if it were live.
6. **Colour never carries meaning alone.** Severity uses colour + label + icon + pattern.
7. **Thumb-first, sunlight-first.** Large targets, high contrast, minimal typing, works
   with one hand and bright outdoor light.
8. **Data cost is a design constraint.** No autoplay, no oversized images, no unnecessary
   polling.
9. **Chat is a wrapper, not an authority.** The conversation is the fastest way to send a
   photo, but the reply is the same `AssessmentCard` used elsewhere. Chat never becomes a
   free-form diagnosis or treatment conversation.

---

## 2. Wording rules

### Use / avoid

| Use | Avoid | Why |
|---|---|---|
| Photo assessment | Diagnosis, detection result | Implies clinical certainty |
| Possible symptom match | Confirmed disease | Overstates evidence |
| Area outlook | Outbreak alert, outbreak warning | Implies confirmed event |
| No assessment / cannot assess this photo | Unknown disease, failed | Abstention is a legitimate outcome |
| Low / moderate / high / urgent risk | Danger level, outbreak level | Operational, not epidemiological |
| Data coverage: good / partial / low | Confidence: 92% | Coverage is honest; unvalidated percentages are not |
| Updated 3 hours ago | Live, real-time | Freshness must be explicit |
| Not enough data for this area yet | No risk | Absence of data ≠ absence of disease |
| Inspect plants and compare with the advisory | Spray this | Liability boundary |
| Ask an extension worker to visit | (no escalation path) | Human route must be visible |

### Forbidden copy

- Any statement that a result is laboratory-confirmed or a confirmed outbreak.
- Percentage confidence unless calibration has been validated and approved for display.
- Pesticide, fungicide, herbicide or fertiliser names, doses, mixtures, intervals or
  "apply X ml per litre".
- "Guaranteed", "safe", "accurate", "prevents crop loss".
- Blaming the farmer for image quality ("you took a bad photo"); use neutral guidance.
- Any implication that low risk means the crop is healthy.

### Tone

- Calm, specific, second person, short sentences.
- Local language first; keep a glossary of agronomic terms approved by the local expert.
- Numbers always carry units and a time reference.
- Do not use "AI" as an authority claim. Describe what the system observed.

### Canonical examples

**Photo assessment (abstained):**
> **No assessment yet**
> This photo is too blurry to compare with known symptoms. Retake it in daylight, holding
> the phone steady about 30 cm from the affected leaf.
> [Retake photo] [Ask an extension worker]

**Photo assessment (result):**
> **Possible symptom match: late blight**
> This is an automated visual comparison, not a diagnosis. Photo quality: good.
> Confidence: medium (calibrated on field data).
> Also considered: early blight, nutrient deficiency.
> **Next step:** inspect 10 plants across the field and compare with the approved
> advisory. If symptoms are spreading, request expert review.
> *Assessment generated 6 Nov 2026, 09:14. Model photo-0.3.1.*

**Area outlook:**
> **Area outlook: moderate risk of late blight**
> For potato in [block name], next 7 days. Issued 6 Nov, valid to 13 Nov.
> **Why:** recent rainfall and current crop stage match conditions associated with this
> disease.
> **Data coverage:** partial — 4 verified reports in this block in the last 14 days.
> Low risk does not mean the disease is absent.
> [Read prevention advisory] [Report what you see]

**Coverage / no-score:**
> **Outlook not available**
> Weather data for this area is more than 48 hours old. We do not issue an outlook from
> stale inputs. Last attempt: 6 Nov, 06:00.

**Chat reply (assessed):**
> **Assistive photo assessment — not a diagnosis**
> Possible symptom match: late blight (medium confidence, not yet calibrated).
> Also considered: early blight, nutrient deficiency.
> The photo passed the quality check. A person has not reviewed this case.
> **Next safe step:** inspect 10 plants and compare with the approved advisory. If symptoms
> are spreading, request expert review.
> [Add context] [Request expert review] [Read advisory]
> *Generated 6 Nov 2026, 09:14. Model photo-0.3.1.*

**Chat reply (abstained):**
> **No assessment yet**
> This photo is too blurry to compare with known symptoms.
> [Retake photo] [Ask an extension worker]

The chat must not add an area outlook to these replies. When an outlook is relevant it is a
separate `OutlookCard`, opened from a link, with its own timestamp and coverage.

---

## 3. Tokens

Single source of truth: `design/tokens.json` (created at scaffold), consumed by Tailwind
(web) and `ThemeData` (Flutter). Do not hard-code values in components.

### Colour (semantic, not decorative)

| Token | Meaning | Notes |
|---|---|---|
| `surface.default` | Page background | |
| `surface.raised` | Card | |
| `surface.sunken` | Grouped sections | |
| `text.primary` / `text.secondary` / `text.disabled` | Text hierarchy | Contrast ≥ 4.5:1 |
| `border.subtle` / `border.strong` | Dividers, inputs | |
| `brand.primary` | Primary action | Not used for severity |
| `risk.low` | Low risk | Always paired with label + icon |
| `risk.moderate` | Moderate risk | |
| `risk.high` | High risk | |
| `risk.urgent` | Urgent risk | |
| `risk.insufficient` | No score / insufficient data | Neutral grey, never red |
| `status.pending` / `status.verified` / `status.rejected` | Case state | Distinct from risk |
| `feedback.error` / `feedback.warning` / `feedback.success` | System messages | |

Rules:

- Risk colour is never reused for case status or brand emphasis.
- `risk.insufficient` must not look like "safe" (avoid green) or "danger" (avoid red).
- Every risk chip includes text and an icon. Map layers use pattern/hatch as well as
  colour.
- Dark mode is out of scope for v1; do not build half of it.

### Typography

| Role | Web | Mobile |
|---|---|---|
| Display | 32/40 semibold | 28/36 semibold |
| H1 | 24/32 semibold | 22/30 semibold |
| H2 | 20/28 semibold | 18/26 semibold |
| Body | 16/24 regular | 16/24 regular |
| Small | 14/20 regular | 14/20 regular |
| Caption | 12/16 regular | 12/16 regular |

- Minimum body size 16 on mobile.
- No text below 12 anywhere.
- Numerals tabular in tables and metrics.
- Line length 60–75 characters on web.

### Spacing, radius, elevation

- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64.
- Radius: 8 (controls), 12 (cards), 999 (chips).
- Elevation: flat by default; one raised level for cards; no decorative shadows.
- Mobile touch target: ≥ 48 × 48 dp, ≥ 8 dp between targets.
- Web control height: 40 px default, 48 px for primary actions.

---

## 4. Component inventory

Shared web components live in `/components`; Flutter equivalents in
`mobile/lib/ui/components/`. Each component has states, not variants-by-boolean.

### Core

| Component | Purpose | Required states |
|---|---|---|
| `Button` | Actions | default, hover, focus, pressed, disabled, loading |
| `Card` | Grouped content | default, interactive, disabled |
| `RiskChip` | Risk band | low, moderate, high, urgent, insufficient |
| `ConfidenceBand` | Qualitative confidence | low, medium, high, not-calibrated |
| `CoverageIndicator` | Data coverage | good, partial, low, unknown |
| `FreshnessBadge` | Data age | fresh, aging, stale, expired |
| `StatusChip` | Case/verification state | queued, syncing, synced, pending_review, confirmed, probable, rejected, duplicate, needs_visit, unresolved |
| `QualityFeedback` | Image quality result | pass, blurry, dark, overexposed, low_resolution, no_plant |
| `StaleBanner` | Cached/expired data | stale, expired |
| `OfflineBanner` | Connectivity | offline, reconnecting, queued |
| `EmptyState` | No content | with action |
| `ErrorState` | Recoverable failure | message, retry, support path |
| `AssessmentCard` | Photo assessment | result, abstained, pending, unsupported_crop |
| `OutlookCard` | Area outlook | scored, insufficient_data, stale |
| `ChatComposer` | Chat image + optional context | idle, attaching, uploading, queued, offline, error |
| `MessageBubble` | One chat message | user, assistant, queued, failed, deleted |
| `AssessmentMessage` | Assistant reply in a thread | assessed, abstained, unsupported_crop, queued, failed, review_requested |
| `ReviewDecisionForm` | Expert decision | edit, submitting, error, locked |
| `QueueRow` | Review queue item | unassigned, assigned, escalated, overdue |
| `MapLegend` | Layer meaning | per layer set |
| `DataTable` | Admin/queue tables | loading, empty, error, paginated |

### Non-negotiable component behaviour

- `AssessmentCard` and `OutlookCard` never render in the same visual container and never
  share a title.
- `RiskChip` requires a text label; icon-only risk is prohibited.
- `StaleBanner` is dismissible only for the session, never permanently.
- `ReviewDecisionForm` disables submit until required evidence is present.
- `QualityFeedback` never blocks the user from saving a report offline; it only blocks
  assessment.
- `AssessmentMessage` renders from structured `kind` fields, never from parsed prose. It
  reuses `AssessmentCard` content and never adds free-form medical or chemical advice.
- `ChatComposer` keeps the image and context when a send fails, and a retry reuses the same
  `client_message_id`.
- A chat reply can link to an `OutlookCard` but can never embed it in the same bubble.

---

## 5. Screen inventory

### Mobile (Flutter)

| Screen | Spec | Key states |
|---|---|---|
| Onboarding / consent | 03-auth-and-roles | new, consent-required, offline |
| Chat list | 08-conversational-capture | list, empty, offline, unread |
| Chat thread | 08-conversational-capture | empty, composing, uploading, queued, replying, assessed, abstained, unsupported, failed |
| Home | 02-reporting-and-capture | fresh outlook, stale outlook, no outlook, offline |
| Crop & field context | 02-reporting-and-capture | defaults, unknown values allowed |
| Capture | 02-reporting-and-capture | camera, gallery, permission denied, low storage |
| Quality feedback | 02-reporting-and-capture | pass, retake-required, cannot-assess |
| Submitting | 02-reporting-and-capture | uploading, queued, retrying, failed |
| Result | 02-reporting-and-capture | assessment, abstained, unsupported, forecast stale |
| History | 02-reporting-and-capture | list, empty, offline, sync error |
| Case detail | 02-reporting-and-capture | pending, reviewed, corrected |
| Advisory | 07-advisory-and-alerts | available, expired, not-approved-for-area |
| Alert preferences | 07-advisory-and-alerts | enabled, disabled, channel unavailable |

### Web — conversational capture (any signed-in user)

| Screen | Spec | Key states |
|---|---|---|
| `/chat` | 08-conversational-capture | list, empty, loading, error |
| `/chat/[conversationId]` | 08-conversational-capture | empty, composing, uploading, queued, replying, assessed, abstained, unsupported, failed |
| Image attachment | 08-conversational-capture | picker, drag-drop, preview, upload error |

### Web — expert portal

| Screen | Spec | Key states |
|---|---|---|
| Login / MFA | 03-auth-and-roles | credentials, mfa, locked, session-expired |
| Review queue | 04-expert-review | loading, empty, filtered, overdue |
| Case detail | 04-expert-review | unassigned, assigned-to-me, locked, decided |
| Decision form | 04-expert-review | editing, validation error, submitting, submitted |
| Escalation | 04-expert-review | pending, accepted, declined |

### Web — district dashboard

| Screen | Spec | Key states |
|---|---|---|
| Overview | 06-forecast-and-risk-map | loading, no-data, partial-coverage |
| Map | 06-forecast-and-risk-map | layers, filtered, stale, zoom-limited |
| Forecast detail | 06-forecast-and-risk-map | scored, insufficient-data, expired |
| Coverage panel | 06-forecast-and-risk-map | good, partial, low |
| Export | 05-data-layer | permitted, role-blocked, audited |

---

## 6. State matrix (apply to every data-bearing screen)

| State | Visual | Copy pattern | Action |
|---|---|---|---|
| Loading | Skeleton, no spinner-only screens | — | — |
| Empty | Illustration + one sentence | "No reports yet in this area." | Primary action |
| Fresh | Normal | "Updated 2 hours ago" | — |
| Aging | Subtle badge | "Updated 20 hours ago" | — |
| Stale | `StaleBanner` | "This outlook expired on …" | Refresh |
| Offline | `OfflineBanner` | "You are offline. Reports will send when connected." | View queue |
| Queued | `StatusChip: queued` | "Saved on this phone." | Retry now |
| Assistant replying | Typing/placeholder in the thread, composer stays usable | "Assessing the photo…" | Cancel / leave |
| Chat assessed | `AssessmentMessage` | "Assistive photo assessment — not a diagnosis." | Add context / review / advisory |
| Chat queued | `MessageBubble: queued` | "Will assess when connected." | View queue |
| Chat failed | `ErrorState` in the bubble | "Could not send. Your photo is saved." | Retry |
| Syncing | Progress + cancel | "Sending…" | Cancel |
| Sync failed | `ErrorState` | "Could not send. We will retry." | Retry |
| Abstained | Neutral card, no risk colour | "No assessment for this photo." | Retake / escalate |
| Insufficient data | `risk.insufficient` | "Not enough data for this area." | Explain why |
| Unsupported | Neutral card | "This crop is not supported yet." | Supported list |
| Error | `ErrorState` | What happened + what to do | Retry / support |
| Unauthorised | Blocked view | "You do not have access." | Back |

Stale, insufficient and abstained are **not** error states and must not use error styling.

---

## 7. Map rules

- Layers are independently toggleable: **verified reports**, **unverified reports**,
  **modelled risk**, **coverage**, **boundaries**.
- Default view: verified reports + modelled risk, never merged into one fill.
- Modelled risk uses a bounded fill with pattern; reports use point/graduated symbols.
- Legend is always visible and states issue time, horizon, source and coverage.
- Clicking an area opens a panel listing each layer's value separately.
- Small counts are suppressed (`n < threshold`) and shown as "suppressed".
- Zoom is capped at the aggregation level; do not allow zooming to farm precision.
- No exact farm points for non-admin roles.
- Empty area copy: "No verified reports in this period. This does not mean the area is
  disease-free."

---

## 8. Accessibility

- WCAG 2.1 AA: contrast ≥ 4.5:1 for body text, 3:1 for large text and UI boundaries.
- Keyboard operable on web; visible focus ring; logical tab order.
- Screen reader labels for icons, risk chips and map controls.
- Do not rely on colour, position or animation alone.
- Respect reduced-motion preference; animations ≤ 200 ms and non-essential.
- Forms: label above field, error text adjacent, `aria-describedby` wired.
- Mobile: support system font scaling to 200% without clipping primary actions.
- Test with one low-vision and one low-literacy user per design round.

---

## 9. Localisation

- v1 ships **one** local language plus English for staff tooling.
- All strings externalised (ARB for Flutter, message catalogs for web).
- Agronomic terms reviewed by a local expert, not machine-translated.
- Allow 40% text expansion; no fixed-width buttons with text.
- Dates: local format in UI, ISO in API. Relative times ("2 hours ago") always paired
  with an absolute timestamp on detail views.
- Numbers: local digits where appropriate; keep units unambiguous (mm, °C, days).

---

## 10. Mobile field constraints

- Target device: low-cost Android, 2–3 GB RAM, Android 10+.
- Camera: support rear camera, tap-to-focus, flash toggle, gallery import.
- Compression target: retain lesion detail; cap long edge at a documented value and
  record the original; never upscale.
- Bright sunlight: high contrast, avoid light-grey-on-white, large type.
- Gloves/wet hands: large targets, no precision drag gestures.
- Data cost: show an estimate before upload when on mobile data; allow "send on Wi-Fi".
- Battery: no background GPS tracking; capture approximate area from saved selection.
- Storage: warn before queue exceeds a configured size; never silently drop reports.

---

## 11. Design QA checklist

- [ ] Photo assessment and area outlook are visually and verbally separate.
- [ ] Uncertainty, coverage and freshness are present on every result.
- [ ] Abstention path exists and is styled as neutral, not as failure.
- [ ] Severity readable without colour.
- [ ] All states in §6 implemented for new screens.
- [ ] Copy passes the use/avoid table; no forbidden claims.
- [ ] Touch targets ≥ 48 dp; contrast checked.
- [ ] Strings externalised; no hard-coded copy.
- [ ] Offline and stale behaviour demonstrated, not just described.
- [ ] Map layers separable and legend complete.

---

## 12. Product surface detail

### 12.1 Farmer mobile application

The field interface must be quick, forgiving and usable in bright outdoor conditions. Reduce
typing; distinguish required from optional information; never block saving a report because
a field is unknown.

| Screen | Must contain | Must not do |
|---|---|---|
| Onboarding / consent | Plain-language purpose, retention, who sees data, one-time consent | Bundle optional research consent with core access |
| Home | Registered crops, local outlook, report button, recent cases, alert preferences, queued count | Show a cached outlook without a freshness cue |
| Crop & field context | Crop from supported list, approximate area, optional variety/stage/area/notes | Require precise coordinates or force a stage |
| Capture | Framing and lighting guidance, focus, flash toggle, gallery import, retake | Take a photo without guidance |
| Quality feedback | Plain reason and a concrete retake instruction | Blame the user or discard the report |
| Submitting | Uploading / queued / retrying / failed, with a retry path | Turn a queued report into a "failed" error |
| Result | Separate photo assessment and area outlook cards, uncertainty, next step, escalation | Merge the two outputs into one score |
| History | Date, crop, sync state, verification state, thumbnail, reviewer response | Show stale data as live |
| Case detail | Original image, assessment at submission, review outcome in plain language | Re-render an old assessment as current |
| Advisory | Approved content, version, validity, escalation | Show unapproved or generated text |
| Alert preferences | Channel, target opt-ins, quiet hours, language | Re-enable a channel after opt-out |

Design rules:

- Use local-language labels plus icons; never icon-only risk.
- Do not use colour alone for severity.
- Make stale cached forecasts visibly different from fresh data, including offline.
- Keep primary actions reachable one-handed; sticky bottom action on mobile.
- Estimate data cost before upload and offer "send on Wi-Fi".

### 12.2 Expert review portal

The portal turns observations into verified evidence efficiently, without hiding evidence or
model limits.

- **Queue management:** sort by urgency, geography, crop, target, age and uncertainty;
  allow assignment and escalation; show backlog, median age and overdue count.
- **Case detail:** original image at full resolution, crop context, capture date, quality
  flags, model candidates with qualitative confidence, model version, forecast context at
  report time, prior cases (privacy-scoped), and model limitations in the model block — not
  behind a tooltip.
- **Verification workflow:** `confirmed`, `probable`, `rejected`, `duplicate`, `needs_visit`,
  `unresolved`. Evidence requirements per decision are in
  `../feature-specs/04-expert-review.md` §7.
- **Feedback capture:** corrected class, severity, field observations, optional lab
  confirmation as a separate evidence tier.
- **Governance:** reviewer identity, timestamps, edits, advisory approvals and every
  transition are logged.
- **Anti-patterns:** never auto-convert a model prediction into a verified label; always
  provide a way to request a better image or more field detail.

### 12.3 Regional dashboard and GIS

The dashboard supports situational awareness. It must make observed reports and modelled
risk unmistakably different.

- **Layers:** verified reports, unverified reports, modelled risk, coverage, boundaries —
  independently toggleable.
- **Filters:** crop, target, date range, risk band, verification status, administrative
  level.
- **Summary panels:** new reports, verified cases, forecast distribution, data freshness,
  review backlog.
- **Privacy:** aggregate locations, suppress small counts, cap zoom at the aggregation level,
  no exact farm points for non-admin roles.
- **Interpretation:** show legend, issue time, horizon, source and coverage. Clicking an
  area lists each layer's value separately.
- **Empty area copy:** "No verified reports in this period. This does not mean the area is
  disease-free."

---

## 13. Appendix wording templates

Canonical approved wording for the two outputs lives in `appendices.md` (Appendices A and B).
Use it verbatim after localisation review; do not paraphrase into a stronger claim.

| Output | Required disclaimer |
|---|---|
| Photo assessment | "This is an automated visual assessment, not a confirmed diagnosis." |
| Area outlook | "This is an early warning, not confirmation that your field is infected." |
| Low risk | "Low risk does not mean the disease is absent." |
| Abstention | "No assessment yet" with a concrete reason and next step. |

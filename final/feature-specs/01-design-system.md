# 01 — Design system

**Status:** Draft
**Owner:** Design lead (TBD)
**Depends on:** `ui-context.md`
**Implements:** consistent, accessible, honest presentation across mobile, expert portal and
district dashboard.

---

## 1. Purpose

Provide one token and component vocabulary so that:

- the two AI outputs are always visually and verbally distinct;
- uncertainty, coverage and freshness are never optional decoration;
- mobile and web look like the same product without sharing an implementation;
- accessibility and localisation are structural, not retrofitted.

This spec defines **contracts**, not final pixel values. Values live in
`design/tokens.json` once scaffolding exists.

---

## 2. Token contract

`design/tokens.json` is the single source. Generated outputs:

| Target | Consumer | Generated artefact |
|---|---|---|
| Web | Tailwind config + CSS variables | `web/styles/tokens.css` |
| Mobile | Flutter theme | `mobile/lib/src/theme.dart` (to be created from `design/tokens.json`) |
| Docs | This spec / storybook | table export |

Token groups and naming:

```
color.surface.{default,raised,sunken,overlay}
color.text.{primary,secondary,disabled,inverse}
color.border.{subtle,strong,focus}
color.brand.{primary,primaryHover,onPrimary}
color.risk.{low,moderate,high,urgent,insufficient}
color.status.{queued,syncing,synced,pending_review,confirmed,probable,rejected,duplicate,needsVisit,unresolved}
color.feedback.{error,warning,success,info}
font.family.{sans,mono}
font.size.{display,h1,h2,body,small,caption}
font.lineHeight.{...}
space.{1,2,3,4,6,8,12,16}   # 4,8,12,16,24,32,48,64
radius.{control,card,chip}
motion.duration.{fast,base}
motion.easing.{standard}
breakpoint.{sm,md,lg,xl}
```

### Rules

- Components reference semantic tokens only (`color.risk.high`), never raw palette values.
- Adding a token requires a use case in this spec and a note in `progress-tracker.md`.
- `risk.*` and `status.*` are disjoint namespaces. A component may not accept a `status`
  value in a `risk` prop or vice versa.
- No dark theme in v1. Do not ship partial dark tokens.

### Risk and status are different axes

| Axis | Values | Meaning |
|---|---|---|
| Risk (forecast only) | low, moderate, high, urgent, insufficient | Area-level outlook |
| Status (case only) | queued, syncing, synced, pending_review, confirmed, probable, rejected, duplicate, needs_visit, unresolved | Report lifecycle |

A verified case does **not** become "high risk". A high-risk forecast does **not** verify a
case. Components must not imply a shared scale.

---

## 3. Component contracts

Each component is defined by: purpose, props (semantic), states, accessibility, and
prohibited usage. Implementations must match these contracts in both platforms unless
explicitly marked platform-specific.

### 3.1 `Button`

| Prop | Type | Notes |
|---|---|---|
| `variant` | `primary \| secondary \| ghost \| danger` | `danger` only for destructive admin actions |
| `size` | `md \| lg` | `lg` required on mobile primary actions |
| `state` | `default \| hover \| focus \| pressed \| disabled \| loading` | Derived, not all passed |
| `fullWidth` | boolean | Mobile primary actions |

- Loading keeps width stable and disables repeated activation.
- Icon-only buttons require an accessible label.
- Minimum target: 48 dp mobile / 40 px web (48 px primary).

### 3.2 `Card`

- Variants: `default`, `interactive`, `disabled`.
- No nested interactive cards.
- `AssessmentCard` and `OutlookCard` are separate components, not `Card` variants.

### 3.3 `RiskChip`

| Prop | Type |
|---|---|
| `band` | `low \| moderate \| high \| urgent \| insufficient` |
| `label` | string (required) |
| `showIcon` | boolean (default true) |

- Must render text. Icon-only is prohibited.
- `insufficient` uses neutral styling, never green or red.
- Screen reader text: "Risk band: moderate" (not "moderate" alone).

### 3.4 `ConfidenceBand`

| Prop | Type |
|---|---|
| `band` | `low \| medium \| high \| not_calibrated` |
| `calibrationNote` | string optional |

- Displays a word plus a short explanation on detail views.
- `not_calibrated` renders "not yet calibrated" and must not be shown as a percentage.
- No numeric percentage prop exists in v1.
- Bands are derived from the D8 decision function on calibrated probabilities: the top
  candidate must clear its class threshold `τ_c`, the top-1/top-2 margin and the entropy
  limit, and the image must not breach the OOD score. A breach is an abstention, not a
  low-confidence band.
- If D8 calibration is not approved, only `not_calibrated` is shown and no band implies a
  probability.

### 3.5 `CoverageIndicator`

| Prop | Type |
|---|---|
| `level` | `good \| partial \| low \| unknown` |
| `detail` | string optional (e.g. "4 verified reports, 14 days") |

- Always paired with a link/expandable explanation of what coverage means.
- `low` must not be styled as an error; it is a data limitation.

### 3.6 `FreshnessBadge`

| Prop | Type |
|---|---|
| `updatedAt` | ISO timestamp |
| `validTo` | ISO timestamp optional |
| `state` | `fresh \| aging \| stale \| expired` (derived) |

- Relative time always paired with absolute time on detail views.
- `stale`/`expired` trigger `StaleBanner` on the containing screen.

### 3.7 `StatusChip`

- Values as listed in §2.
- Sync states (`queued`, `syncing`, `synced`) are distinct from review states.
- A single chip shows one axis only; do not combine "synced + confirmed".

### 3.8 `QualityFeedback`

| Prop | Type |
|---|---|
| `result` | `pass \| blurry \| dark \| overexposed \| low_resolution \| no_plant` |
| `guidance` | string |

- Explains what to change and offers retake.
- Does not block saving the report offline.
- Neutral tone; never blames the user.

### 3.9 `AssessmentCard`

| Prop | Type |
|---|---|
| `state` | `pending \| assessed \| abstained \| unsupported_crop \| failed` |
| `candidates` | array of `{label, band}` (max 3) |
| `quality` | `QualityFeedback` result |
| `confidence` | `ConfidenceBand` |
| `abstainReason` | enum, required when `state = abstained` |
| `modelVersion` | string |
| `generatedAt` | timestamp |
| `onRetake`, `onEscalate` | actions |

- Title is always "Photo assessment" (localised).
- `abstained` has no candidate list and no risk colour.
- `abstainReason` is a machine code rendered as plain-language copy: `below_class_threshold`,
  `low_margin`, `high_entropy`, `out_of_distribution`, `unsupported_crop`,
  `quality_gate_failed`. Never a free-text guess.
- Must include "not a diagnosis" in the body, not only in a tooltip.
- No control on this card changes the model state. Retake creates a new assessment; escalate
  opens manual review. Neither rewrites the abstained prediction (D8).

### 3.10 `OutlookCard`

| Prop | Type |
|---|---|
| `state` | `scored \| insufficient_data \| stale \| expired` |
| `band` | `RiskChip` value (scored only) |
| `horizon` | `{from, to}` |
| `drivers` | string[] |
| `coverage` | `CoverageIndicator` |
| `issueTime`, `modelVersion` | required |

- Title is always "Area outlook" (localised).
- Never renders candidate classes.
- `insufficient_data` shows the reason and last attempt time.
- Must include "Low risk does not mean the disease is absent."

### 3.11 `StaleBanner` / `OfflineBanner`

- `StaleBanner`: persistent until data refreshes; dismissible for session only.
- `OfflineBanner`: appears within 2 s of connectivity loss; shows queued count.
- Both are non-modal and must not cover primary actions.

### 3.12 `QueueRow`

| Prop | Type |
|---|---|
| `observationId`, `crop`, `targetCandidates`, `age`, `urgency`, `coverageHint`, `assignment` | |
| `state` | `unassigned \| assigned \| escalated \| overdue` |

- Urgency is derived from config (severity + uncertainty + age), not hard-coded.
- Row must expose enough context to triage without opening the case.

### 3.13 `ReviewDecisionForm`

- Fields: decision, corrected label (conditional), severity (conditional), evidence notes
  (required for `confirmed`, `rejected`, `needs_visit`), field observations, lab
  confirmation (optional, separate evidence tier).
- Submit disabled until required evidence is present.
- Decision options come from the server (state machine), not hard-coded in the client.
- Shows a warning when the decision contradicts the model's top candidate.

### 3.14 `MapLegend`

- Renders one entry per active layer, with source, issue time, horizon, coverage.
- Pattern swatches for modelled risk; symbols for reports.
- Must state "reports and modelled risk are different evidence".

### 3.15 `EmptyState` / `ErrorState`

- `EmptyState`: one sentence + one action. Never a bare "No data".
- `ErrorState`: what happened, what to do, retry, support path, request ID (web).
- `ErrorState` is not used for abstention, stale data or low coverage.

---

## 4. Layout and responsive rules

| Breakpoint | Width | Use |
|---|---|---|
| `sm` | < 640 | Mobile web (not primary) |
| `md` | 640–1023 | Tablet |
| `lg` | 1024–1439 | Expert portal |
| `xl` | ≥ 1440 | Dashboard with side panels |

- Expert portal: queue list + detail pane at `lg+`; stacked at `md`.
- Dashboard: map dominant, filter rail left, summary right; collapse rail below `lg`.
- Max content width 1280 px; data tables scroll horizontally rather than compress.
- Mobile: single column, sticky primary action at bottom, safe-area aware.

---

## 5. Iconography and illustration

- One icon family (outline, 24 px grid) shared across platforms.
- Icons always paired with text for risk, status and navigation.
- Do not use insect/leaf emoji as status indicators.
- Illustrations only for empty/onboarding states; no stock photos of healthy crops that
  could be mistaken for evidence.

---

## 6. Platform mapping

| Concern | Web | Mobile |
|---|---|---|
| Tokens | CSS variables + Tailwind theme | `ThemeExtension` + generated constants |
| Primitives | shadcn/ui as base, restyled to tokens | Material 3 base, restyled |
| Icons | Lucide | Material Symbols (matching set) |
| Charts | Recharts or visx | fl_chart |
| Maps | MapLibre GL JS | Static map image / deep link in v1 (no map editing) |
| Motion | CSS transitions ≤ 200 ms | implicit animations ≤ 200 ms |
| Storybook | Storybook per component + state | Flutter widget tests; Widgetbook optional |

A component is not "done" until every state in its contract has a story/golden.

---

## 7. Content patterns

- **Dates:** relative + absolute on detail (`2 hours ago · 6 Nov 2026, 09:14`).
- **Numbers:** thousands separators; units always (`12 mm`, `7 days`); no bare decimals
  for probabilities in v1.
- **Model version:** monospace, small, with a "what is this?" affordance.
- **Errors:** state the user action first, then the cause.
- **Truncation:** never truncate a risk label or coverage level; truncate notes with an
  expand control.
- **Pluralisation:** use ICU message format.

---

## 8. Acceptance criteria

- [ ] `design/tokens.json` exists and generates both web and mobile artefacts.
- [ ] Every component in §3 has a documented state matrix and a story/golden per state.
- [ ] `AssessmentCard` and `OutlookCard` share no container and no title string.
- [ ] Risk and status namespaces are separate in types and cannot be cross-passed.
- [ ] Risk is distinguishable with colour removed (icon + label + pattern).
- [ ] Contrast passes AA on all token pairings used for text and controls.
- [ ] No component accepts a raw hex value or magic spacing number.
- [ ] All copy is externalised; no hard-coded strings in component code.
- [ ] Touch targets ≥ 48 dp on mobile; focus states visible on web.
- [ ] Storybook builds in CI and is reviewed by design before feature work.

---

## 9. Out of scope

- Dark mode.
- Multi-brand theming.
- Data visualisation library beyond map, chips and simple charts.
- Animation system beyond basic transitions.
- Native iOS-specific design (Android-first).

---

## 10. Open questions

1. Which icon set is available in both Flutter and React (web) without licensing
   friction?
2. Is a shared Storybook pipeline worth the setup cost for a 7-person team?
3. Does the local language require a different font for legibility at small sizes?
4. Should the district dashboard support print/PDF export layouts in v1?

---

## 11. Blueprint traceability

| Blueprint chapter | Where this spec uses it |
|---|---|
| 15 — Farmer mobile application design | Screen inventory §5, component contracts §3 |
| 16 — Expert review portal | `QueueRow`, `ReviewDecisionForm`, screen inventory §5 |
| 17 — Regional dashboard and GIS | `MapLegend`, `DataTable`, screen inventory §5 |
| 32 — Image confidence and explainability | `ConfidenceBand`, `AssessmentCard` states |
| App. B — Sample image assessment wording | §7 content patterns; `../docs-context/appendices.md` |

The token contract is the concrete implementation of the blueprint's design-system intent:
semantic tokens, no raw values, risk and status as separate axes, and every state designed
rather than defaulted.

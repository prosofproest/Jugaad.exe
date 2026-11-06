# 06 — Forecast and risk map

**Status:** Draft
**Owner:** ML lead + agronomist (TBD)
**Depends on:** `05-data-layer.md`, `04-expert-review.md`
**Implements:** area outlook generation, no-score behaviour, risk bands, map layers,
coverage display.

---

## 1. Goal

Produce a defensible, reproducible area-level outlook from weather and crop context, with
honest coverage and freshness, and present it separately from observed reports.

**v1 stance:** a **nowcast** (risk given the last 10 days) is preferred over a 7-day
outlook unless D2 is resolved otherwise. A validated rules model is the baseline; ML is an
overlay only after at least two seasons of verified outcomes.

---

## 2. Task definition (must be completed before implementation)

| Field | Value | Status |
|---|---|---|
| Crop | 1 supported crop | Blocked on D1 |
| Target | 3–5 supported conditions | Blocked on D1 |
| Geography | block/mandal level | Blocked on D1 |
| Horizon | nowcast (default) or 7 days | Blocked on D2 |
| Issue cadence | daily (proposed) | Proposed |
| Event definition | first verified case / incidence threshold / escalation | **Blocked on D1/D5** |
| Negative definition | verified absence within coverage, not "no report" | Required |
| Spatial unit | smallest unit inputs support | Blocked on D1 |
| Primary consumer | extension worker + farmer SMS | Proposed |

**Event definition rule:** write it before feature engineering. Keep different event types
as separate tasks. "No report" is never a negative label.

---

## 3. Inputs

| Family | Examples | Availability rule |
|---|---|---|
| Weather | rainfall, temp min/max, RH, consecutive wet days, leaf-wetness proxy | Must exist at issue time; store `source_timestamp` |
| Crop context | crop, stage, planting window, variety, irrigation | From crop cycle / calendar |
| Seasonal | week of year, monsoon period, days since planting | Deterministic |
| Historical pressure | lagged verified reports, nearby verified reports, prior-season occurrence | Verified only |
| Coverage | active reporters, visits, data completeness | Required for no-score gate |
| Boundaries | versioned admin geometry | Version recorded with forecast |

**Leakage rule:** every feature must be computable at `issue_time`. Store the feature
snapshot; never recompute a historical forecast from today's data.

---

## 4. Model ladder

| Step | Model | When |
|---|---|---|
| 1 | Documented agronomic risk index (weather thresholds + crop stage), versioned and approved | Day one |
| 2 | Logistic regression on weather windows + stage + lagged verified reports | After one season |
| 3 | Gradient boosting (LightGBM/XGBoost) | After 2+ seasons |
| 4 | Spatiotemporal models | Only with dense longitudinal data (year 3+) |

Rules:

- The rules model is always retained as a fallback and comparison baseline.
- Model selection uses temporal holdout; spatial holdout where data allows.
- A more complex model ships only if it beats the baseline on the operational metric, not
  on training loss.

---

## 5. Risk bands and no-score

| Band | Operational meaning | Approved action |
|---|---|---|
| `low` | Conditions not conducive in the window | Routine scouting; no alert |
| `moderate` | Some conducive factors present | Advisory + scouting prompt |
| `high` | Multiple conducive factors, local evidence present | Alert to enrolled users; prioritise visits |
| `urgent` | High + verified local escalation | Alert + escalation owner notified |
| `insufficient_data` | Coverage/freshness below threshold | No outlook; explain why |

Rules:

- Band thresholds live in config with an approval record; no inline numbers.
- `low` never means "no disease present".
- Probability is displayed only when calibration is validated and approved; otherwise
  `probability: null` and a qualitative band.
- Bands and actions are reviewed when the crop calendar, reporting patterns or calibration
  change.

### No-score gate (all must pass)

1. Weather snapshot freshness within threshold for the area.
2. Minimum coverage (active reporters / completeness) met.
3. Crop calendar and stage available.
4. Boundary version matches the configured version.
5. Model version is `approved` in the registry.

If any fails: persist a forecast row with `risk_band = insufficient_data`, a machine
`reason_code`, and `coverage`. Do not impute.

---

## 6. Generation pipeline

```
scheduled job (daily, per crop × target × area)
  ├─ check model approval + config validity
  ├─ load weather snapshots (freshness check)
  ├─ load crop stage + calendar
  ├─ load lagged verified reports (verified only)
  ├─ compute coverage
  ├─ if gate fails → persist insufficient_data row (reason, coverage)
  ├─ else compute features → persist feature_snapshot (immutable)
  ├─ run rules model → band (+ probability if calibrated)
  ├─ persist forecast (issue, valid_from, valid_to, drivers, lineage)
  └─ emit metrics + alert evaluation
```

Idempotency: a run for the same `(crop, target, geo, horizon, issue_date)` must not create
duplicates; re-runs supersede with a new `issue_time` only if explicitly forced, and both
rows are retained.

---

## 7. API

### `GET /v1/forecasts?crop=&target=&geo=&horizon=`

```json
{
  "items": [
    {
      "forecast_id": "fcst_demo_001",
      "crop": "potato",
      "target": "late_blight",
      "geography": {"level": "block", "code": "DEMO_BLOCK_01", "name": "Demo Block"},
      "issue_time": "2026-11-06T06:00:00Z",
      "valid_from": "2026-11-06T06:00:00Z",
      "valid_to": "2026-11-13T06:00:00Z",
      "risk_band": "moderate",
      "probability": null,
      "confidence": "medium",
      "coverage": "partial",
      "coverage_detail": {"verified_reports_14d": 4, "active_reporters": 7},
      "drivers": ["recent_rainfall", "crop_stage"],
      "model_version": "forecast-rules-demo-0.1",
      "feature_snapshot_id": "fs_demo_001",
      "is_stale": false,
      "is_demo": true
    }
  ],
  "next_cursor": null
}
```

`probability` is `null` until calibration is approved. `is_demo` must render a demo badge.

### `GET /v1/map/layers/{layer}?bbox=&crop=&target=&date=`

Layers: `verified_reports`, `unverified_reports`, `modelled_risk`, `coverage`,
`boundaries`. Each returns its own geometry and properties. **No endpoint returns a merged
"risk" layer.**

### `GET /v1/forecasts/{id}`

Full detail: drivers, coverage breakdown, issue/validity, lineage, model version, band
rationale, advisory links.

---

## 8. Map behaviour

| Layer | Geometry | Encoding | Notes |
|---|---|---|---|
| Verified reports | points/clusters at block centroid | symbol, count | Verified only |
| Unverified reports | points/clusters | hollow symbol | Never styled as risk |
| Modelled risk | admin polygons | bounded fill + hatch by band | Separate legend |
| Coverage | admin polygons | neutral sequential scale | "How much do we know", not risk |
| Boundaries | lines | reference | Version label |

Rules:

- Default view shows verified reports **and** modelled risk, visually distinct.
- Legend always states layer, source, issue time, horizon, coverage.
- Clicking an area shows each layer's value in separate rows.
- Small counts suppressed (`n < threshold` → "suppressed").
- Zoom capped at aggregation level; no farm precision.
- Empty area: "No verified reports in this period. This does not mean the area is
  disease-free."

---

## 9. Evaluation

| Metric | Requirement |
|---|---|
| Temporal holdout | Train on earlier seasons, test on the latest complete season |
| Spatial holdout | At least one district/block held out where data allows |
| Discrimination | PR-AUC (primary), precision/recall at shipped band thresholds |
| Calibration | Brier score, reliability diagram, ECE |
| Operational | False alerts per area/time, missed events, lead time vs baseline |
| Coverage sensitivity | Performance reported by coverage level |
| Baseline comparison | Rules model vs logistic vs boosting, same splits |

Report sample counts and per-area results. Never report a single aggregate without the
class/area breakdown.

---

## 10. Alert hand-off

Forecast generation emits eligible candidates to `07-advisory-and-alerts.md`. This spec
does not define message copy, channels, cooldowns or delivery; it only guarantees that
every forecast carries `risk_band`, `coverage`, `issue_time`, `valid_to`, `target`,
`geo_code`, `model_version` and `is_demo`.

---

## 11. Edge cases

| Case | Behaviour |
|---|---|
| Weather provider outage | `insufficient_data` with `weather_stale`; no alert |
| Boundary version mismatch | `insufficient_data` with `boundary_mismatch`; ops alert |
| Crop calendar missing | `insufficient_data` with `calendar_missing` |
| Zero verified reports but good coverage | Valid low/moderate score; coverage shown; never "disease-free" |
| High reports, low coverage | Band capped or `insufficient_data`; coverage shown |
| Model not approved | No forecast generated; job fails loudly |
| Duplicate run | Idempotent; no duplicate current forecast |
| Late-arriving report | Does not rewrite a past forecast; used in the next issue |
| Area split/merged | New codes; historical forecasts retain old code + version |
| Demo environment | `is_demo` true everywhere; excluded from operational alerts |

---

## 12. Acceptance criteria

- [ ] Task definition table is complete and approved before implementation.
- [ ] Rules baseline implemented, versioned and approved by an agronomist.
- [ ] Feature snapshot persisted for every scored forecast.
- [ ] Re-running a forecast from its snapshot reproduces the same band.
- [ ] No-score gate returns `insufficient_data` for each of the five failure conditions.
- [ ] Unverified reports are excluded from features (test with an inserted unverified row).
- [ ] `probability` is null unless calibration is approved.
- [ ] Forecast response includes issue/validity, coverage, drivers, model version.
- [ ] Map layers are independently toggleable and never merged server-side.
- [ ] Small counts suppressed at the configured threshold (test).
- [ ] Expired forecasts are marked stale in API and UI.
- [ ] Demo forecasts are labelled and excluded from operational alerts.
- [ ] Evaluation report includes temporal + spatial holdout, calibration and sample counts.

---

## 13. Out of scope

- Farm-level risk.
- Satellite/drone features.
- Real-time nowcasting from streaming data.
- Multi-crop joint models.
- Automated threshold tuning in production.
- Yield-loss prediction.

---

## 14. Open questions

1. D1/D2 outcomes (crop, targets, horizon) — everything above depends on them.
2. Which validated rules model applies to the chosen crop? (e.g. BLITECAST/SimCast for
   potato late blight; Mills table is apple-specific and not transferable.)
3. Is daily issue cadence supportable by the weather provider's update frequency?
4. What is the minimum coverage threshold that still permits a scored outlook?
5. Does the partner need a 7-day outlook for operational planning even if only a nowcast is
   defensible? If so, label it as experimental.

---

## 15. Blueprint traceability

| Blueprint chapter | Where this spec uses it |
|---|---|
| 23 — Weather and environmental data | §3 inputs, §5 no-score gate |
| 33 — Outbreak forecasting: task definition | §2 task definition |
| 34 — Forecast feature engineering | §3 inputs, §6 pipeline |
| 35 — Forecast model baselines | §4 model ladder |
| 36 — Forecast calibration and thresholds | §5 risk bands, §9 evaluation |
| 37 — Spatial and temporal forecasting | §8 map behaviour |
| 38 — Combining image and forecast outputs | §7 API, §8 map rules |
| 39 — Risk map and geospatial analytics | §8 map behaviour |
| App. C — Example forecast API response | §7 API |

Model design, evaluation and calibration detail is in `../docs-context/ml-models.md`
§§7–12. Data-splitting rules are in `../docs-context/data-foundation.md` §6.

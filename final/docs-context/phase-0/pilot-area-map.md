# Pilot area map and site specification

**Status:** `[x]` Candidate map specification 2026-11-06 — sites and boundary version
pending partner confirmation.
**Pilot cluster:** Kolar, Chikkaballapura and Bengaluru Rural districts, Karnataka.
**Zone:** Karnataka Eastern Dry Zone (agro-climatic Zone 5).
**Machine-readable site list:** [`pilot-sites.csv`](pilot-sites.csv).

> **No boundary geometry is included in this repository.** The licensed boundary dataset
> (DS-007) has not been cleared. This document defines the map contract; it does not
> distribute a boundary file, exact farm location or village-level risk surface.

---

## 1. Administrative hierarchy

```
State (Karnataka)
  └── District (Kolar, Chikkaballapura, Bengaluru Rural)
        └── Taluk
              └── Hobli / block          ← smallest defensible reporting unit
                    └── Village        ← collection context only, never a risk surface
                          └── Farm / field  ← never exposed; exact coordinates restricted
```

**Smallest defensible spatial unit:** hobli/block. It is large enough to reduce
re-identification and small enough to support a local outlook. Village-level and farm-level
risk are out of scope for v1 (project-overview §8; R9).

---

## 2. Site selection

Six candidate hoblis are organised as three matched pairs. One site in each pair is assigned
to the intervention arm and one to the control/baseline arm. Pairing is based on:

- tomato area and season overlap;
- baseline reporting/extension activity;
- agro-climatic similarity within the Eastern Dry Zone;
- verification capacity (`can_confirm` holders reachable);
- road access and field-staff feasibility;
- no shared field boundary that would cause contamination between arms.

| Pair | Intervention site | Control site | Matching rationale |
|---|---|---|---|
| P1 | `PILOT-H01` | `PILOT-H02` | Similar tomato area and extension presence |
| P2 | `PILOT-H03` | `PILOT-H04` | Similar crop calendar and distance to plant clinic |
| P3 | `PILOT-H05` | `PILOT-H06` | Similar baseline reporting and road access |

The actual hobli names, boundary codes and population/area figures are entered only after
the partner and the boundary licence confirm them. `pilot-sites.csv` marks every row
`candidate`.

**Randomisation:** the arm within each pair is assigned by a pre-registered coin flip or
random-number seed recorded by the evaluator. The seed and assignment are stored with the
pre-registration manifest. Sites cannot be reassigned after the first observation without a
recorded amendment.

---

## 3. Map layers

The map is a set of **separate** layers. It never merges reports and predictions into one
"risk" surface (R1).

| Layer | Content | Aggregation | Visibility |
|---|---|---|---|
| Verified reports | Count/share of human-confirmed cases | Hobli/block | All authorised staff; public aggregate only if approved |
| Unverified reports | Count of reports awaiting review | Hobli/block | Staff only |
| Modelled risk | Nowcast band from the approved rules baseline | Hobli/block | Staff; farmer-facing only after limited-alert approval |
| Coverage | Report completeness, freshness and representativeness | Hobli/block | Always visible with any risk band |
| Boundaries | Versioned admin geometry | Hobli/block | Authenticated map only; no raw download |
| No-score | Areas with insufficient data | Hobli/block | Always visible; never coloured as low risk |

**Map rules:**

- The legend states issue time, validity, horizon, coverage and "not a confirmed outbreak".
- A low-coverage area is shown as low coverage, not low risk (R3).
- Small counts are suppressed in the view/function, not only in the UI. The D9 threshold is
  pending; the interim rule is **no cell with fewer than 5 reports is displayed**.
- Exact farm points and village-level case pins are never shown.
- The boundary version is stored with every derived record.

---

## 4. Boundary data contract

| Item | Requirement |
|---|---|
| Source | DS-007 licensed administrative boundary dataset |
| Version | `KA-ADMIN-v1` (proposed label; replace with the provider's release identifier) |
| Levels | State, district, taluk, hobli/block |
| Codes | Stable LGD or provider codes; keep the original code and version |
| Geometry | Valid polygons; no slivers; coastline/state boundary checked |
| Licence | Recorded in the partner register before ingestion |
| Change rule | A boundary change creates a new version; old records keep the version they were assigned |
| Access | Authenticated staff only; no public raw geometry |

**Do not** infer a boundary from a map screenshot, a village list or a hand-drawn polygon.
If the licensed file is unavailable, the map layer stays `not_available` and the pilot uses
the partner's official admin list without spatial rendering.

---

## 5. Privacy and suppression

- Approximate location only; exact coordinates are optional, separately consented and
  restricted by role (R9).
- Images are stripped of GPS EXIF unless the separate exact-location consent applies.
- No farmer name, phone number or farm identifier in a map popup, export or log.
- Small-count suppression applies consistently to the map, API and exports.
- A map cell that could identify one farm is aggregated upward or withheld.
- Biosecurity: the public map does not expose farm vulnerability or exact outbreak location
  (R-13).

---

## 6. Map acceptance checklist

- [ ] Boundary licence recorded and version pinned.
- [ ] Site names and codes match the partner's official list.
- [ ] Six sites, three matched pairs, arm assignment seeded and recorded.
- [ ] Every site has a named verification route before the limited-alert phase.
- [ ] Layers are separate; no merged risk field exists in the API or database view.
- [ ] Coverage is displayed with every risk band.
- [ ] Small-count suppression is enforced server-side.
- [ ] No exact farm geometry in the map, export or logs.
- [ ] A no-score/insufficient-data state is visibly distinct from low risk.

---

## 7. Sign-off

| Role | Name | Decision | Date |
|---|---|---|---|
| Product lead | TBD at workshop | Pending | — |
| Data engineer | TBD at workshop | Pending | — |
| Partner field operations lead | TBD at MoU | Pending | — |
| Legal/privacy reviewer | TBD at MoU | Pending | — |

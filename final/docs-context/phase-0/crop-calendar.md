# Crop calendar and epidemic window — tomato, Eastern Dry Zone

**Status:** `[x]` Documented 2026-11-06 — agronomist sign-off required at Gate 0.
**Crop:** Tomato (*Solanum lycopersicum*).
**Zone:** Karnataka Eastern Dry Zone (agro-climatic Zone 5).
**Pilot district cluster:** Kolar, Chikkaballapura and Bengaluru Rural (final hoblis in
[`pilot-sites.csv`](pilot-sites.csv)).
**Purpose:** align collection, labelling, silent phase and limited-alert phase with the
actual crop and epidemic calendar, not the funding cycle.

> **Boundary.** This is an agronomic planning calendar. It is not a validated forecast model
> and it does not assert that a target will occur. The weather triggers are reference
> conditions for the rules baseline; they must be approved and versioned before Gate 4.

---

## 1. Season summary

| Season | Nursery / transplant | Main growth | Harvest | Primary epidemic relevance |
|---|---|---|---|---|
| Kharif | June–July | July–August | August–September | Early blight, Septoria, leaf curl; late blight if cool wet spells |
| Rabi | October–November | November–December | January–February | **Primary late blight / early blight / Septoria window** |
| Summer | January–February | February–April | April–May | Leaf curl and early blight; late blight low unless unseasonal cool humidity |

**Primary pilot window:** Rabi 2026–27, transplant October–November 2026, epidemic window
**mid-November 2026 to mid-February 2027**. If Gate 0 is not signed by 2026-11-30, the
protocol defers to Kharif 2027 rather than forcing a partial season.

---

## 2. Month-by-month calendar

| Month | Season / operation | Growth stage | Agronomic operations | Targets to watch | Epidemic risk | Notes for the pilot |
|---|---|---|---|---|---|---|
| January | Rabi harvest; summer nursery | Fruiting / harvest | Pick, grade, remove diseased debris, monitor whitefly | Late blight, early blight, Septoria, leaf curl | Late blight high; early blight moderate–high; Septoria high; leaf curl moderate | Limited-alert phase if silent phase passed |
| February | Rabi harvest; summer transplant | Harvest / vegetative | Field sanitation, staking, irrigation check | Late blight, early blight, Septoria, leaf curl | Late blight moderate; early blight moderate; Septoria moderate; leaf curl high | End of primary window; close-out review |
| March | Summer | Vegetative / flowering | Staking, pruning, whitefly monitoring | Leaf curl, early blight | Leaf curl high; early blight moderate; late blight low | Heat and vector pressure; no late-blight alert without evidence |
| April | Summer | Flowering / fruiting | Irrigation, mulch, scout lower leaves | Leaf curl, early blight | Leaf curl high; early blight high; late blight low | Image collection for leaf curl and look-alikes |
| May | Summer harvest | Fruiting / harvest | Pick, sanitise, record yield context | Leaf curl, early blight | Leaf curl high; early blight high; late blight low | Hot/dry look-alikes are common; abstain when unclear |
| June | Kharif nursery / transplant | Nursery / vegetative | Raised nursery, transplant, drainage | Leaf curl, early blight, late blight | Leaf curl high; early blight moderate; late blight low–moderate | Monsoon onset; collection protocol training |
| July | Kharif | Vegetative / flowering | Staking, drainage, scout | Late blight, early blight, leaf curl | Late blight moderate–high in cool wet spells; early blight high; leaf curl high | Secondary late-blight window if night temperatures fall |
| August | Kharif | Flowering / fruiting | Sanitation, airflow, harvest start | Late blight, early blight, Septoria | Late blight high in continuous wet; early blight high; Septoria moderate | Peak Kharif collection window |
| September | Kharif harvest | Fruiting / harvest | Pick, remove debris, record | Early blight, Septoria, leaf curl | Late blight moderate; early blight moderate; Septoria moderate | End of Kharif window |
| October | Rabi nursery / transplant | Nursery / vegetative | Nursery, transplant, soil preparation | Leaf curl, early blight | Late blight low–moderate; early blight low; leaf curl moderate | Pre-pilot training and site readiness |
| November | Rabi | Vegetative / flowering | Staking, irrigation, scout | Late blight, early blight, Septoria | Late blight moderate–high; early blight moderate; Septoria moderate | **Silent phase starts when Gate 0 is signed** |
| December | Rabi | Flowering / fruiting | Sanitation, airflow, harvest start | Late blight, early blight, Septoria | Late blight high; early blight high; Septoria high | **Primary epidemic window** |

---

## 3. Epidemic window

**Primary window:** mid-November to mid-February (Rabi). Cool nights, high relative humidity,
long leaf-wetness periods and a dense canopy favour late blight; early blight and Septoria
also increase as lower leaves senesce.

**Secondary window:** late July to August (Kharif) if the monsoon brings cool, wet spells.
This is a contingency window, not the primary pilot.

**Leaf curl window:** March–May and July–September, associated with whitefly pressure and
hot/dry or warm-humid conditions. Leaf curl is image-assessment eligible but not forecast
eligible in v1.

### 3.1 Reference weather conditions for the rules baseline

These are **reference conditions to be approved and versioned**, not a released model.

| Target | Reference conditions | Source to confirm |
|---|---|---|
| Late blight | Mean temperature roughly 15–22 °C, relative humidity above ~85%, leaf wetness ≥ 8–10 h/day, consecutive wet days | Partner agronomist; published blight rules (for example BLITECAST/SimCast-style) |
| Early blight | Warm, humid periods roughly 24–29 °C with alternating wet/dry leaves; older lower leaves | Partner agronomist; published early-blight rules |
| Septoria leaf spot | Moderate temperatures roughly 20–25 °C with prolonged leaf wetness and splashing rain | Partner agronomist; published Septoria rules |
| Leaf curl | Whitefly pressure, warm dry spells, nearby infected crops; not a weather-only model | Partner agronomist; no forecast claim in v1 |

**Rule:** if the weather source is stale, missing or below the coverage gate, the outlook is
`insufficient_data`. The calendar never substitutes for a missing forecast.

---

## 4. What the pilot must record

For every observation and every site-week:

- Crop stage at capture (nursery, vegetative, flowering, fruiting, harvest, unknown).
- Planting/transplant date, if known; variety is optional.
- Whether the field is in the primary or secondary window.
- Recent weather exposure (rain, humidity, cool nights) from the weather source, not memory.
- Whether the image is from the upper, middle or lower canopy.
- Whether the field has a known history of the target or a look-alike.

---

## 5. Sign-off and change control

- [ ] Agronomist confirms the season windows and growth stages for the pilot districts.
- [ ] Agronomist confirms the epidemic window and reference weather conditions.
- [ ] Partner confirms the actual transplant/harvest dates in the pilot sites.
- [ ] The protocol timeline is checked against the confirmed calendar.
- [ ] Any change is recorded in `progress-tracker.md` §7 and the pre-registration manifest is
      regenerated if it affects D5 or the pilot protocol.

**Sign-off**

| Role | Name | Decision | Date |
|---|---|---|---|
| Agronomist / pathologist | TBD at workshop | Pending | — |
| Partner field operations lead | TBD at MoU | Pending | — |

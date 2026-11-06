"use client";

import { useMemo, useState } from "react";

import { formatDate } from "@/lib/format";
import { useWorkspace, severityTone } from "@/lib/workspace/store";
import type { HotspotCase, RiskBand, Severity } from "@/lib/workspace/types";

import { Badge, Icon, RiskPill, Segmented } from "./ui";

function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

function riskClass(band: RiskBand): string {
  return `ws-risk-${band}`;
}

export function HotspotMap() {
  const { state } = useWorkspace();
  const [pest, setPest] = useState("all");
  const [crop, setCrop] = useState("all");
  const [district, setDistrict] = useState("all");
  const [windowDays, setWindowDays] = useState<"7" | "14" | "30">("14");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [severity, setSeverity] = useState<"all" | Severity>("all");
  const [selected, setSelected] = useState<HotspotCase | null>(null);

  const pests = unique(state.cases.map((item) => item.pest));
  const crops = unique(state.cases.map((item) => item.crop));
  const districts = unique(state.cases.map((item) => item.district));

  const cutoff = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() - Number(windowDays));
    return date;
  }, [windowDays]);

  const cases = useMemo(
    () =>
      state.cases.filter((item) => {
        const reported = new Date(item.reportedAt);
        if (reported < cutoff) return false;
        if (pest !== "all" && item.pest !== pest) return false;
        if (crop !== "all" && item.crop !== crop) return false;
        if (district !== "all" && item.district !== district) return false;
        if (verifiedOnly && !item.verified) return false;
        if (severity !== "all" && item.severity !== severity) return false;
        return true;
      }),
    [state.cases, cutoff, pest, crop, district, verifiedOnly, severity],
  );

  const regions = useMemo(
    () =>
      state.riskRegions.filter((region) => {
        if (pest !== "all" && region.pest !== pest) return false;
        if (crop !== "all" && region.crop !== crop) return false;
        if (district !== "all" && region.district !== district) return false;
        return true;
      }),
    [state.riskRegions, pest, crop, district],
  );

  const totalCases = cases.reduce((sum, item) => sum + item.cases, 0);
  const verifiedCases = cases.filter((item) => item.verified).reduce((sum, item) => sum + item.cases, 0);
  const nearby = [...cases].sort((a, b) => b.cases - a.cases).slice(0, 4);

  return (
    <div className="ws-hotspot">
      <div className="ws-filter-bar">
        <label className="ws-filter">
          <span>Pest</span>
          <select value={pest} onChange={(event) => setPest(event.target.value)}>
            <option value="all">All pests</option>
            {pests.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="ws-filter">
          <span>Crop</span>
          <select value={crop} onChange={(event) => setCrop(event.target.value)}>
            <option value="all">All crops</option>
            {crops.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="ws-filter">
          <span>District</span>
          <select value={district} onChange={(event) => setDistrict(event.target.value)}>
            <option value="all">All districts</option>
            {districts.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="ws-filter">
          <span>Reported</span>
          <select value={windowDays} onChange={(event) => setWindowDays(event.target.value as "7" | "14" | "30")}>
            <option value="7">Last 7 days</option>
            <option value="14">Last 14 days</option>
            <option value="30">Last 30 days</option>
          </select>
        </label>
        <label className="ws-filter">
          <span>Severity</span>
          <select value={severity} onChange={(event) => setSeverity(event.target.value as "all" | Severity)}>
            <option value="all">All severities</option>
            <option value="low">Low</option>
            <option value="moderate">Moderate</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </label>
        <label className="ws-check">
          <input
            type="checkbox"
            checked={verifiedOnly}
            onChange={(event) => setVerifiedOnly(event.target.checked)}
          />
          Expert-verified only
        </label>
      </div>

      <div className="ws-hotspot-stats">
        <div>
          <span>Reported cases</span>
          <strong>{totalCases}</strong>
        </div>
        <div>
          <span>Verified cases</span>
          <strong>{verifiedCases}</strong>
        </div>
        <div>
          <span>Active hotspots</span>
          <strong>{cases.length}</strong>
        </div>
        <div>
          <span>Window</span>
          <strong>{windowDays} days</strong>
        </div>
      </div>

      <div className="ws-hotspot-grid">
        <div className="ws-map-canvas ws-hotspot-canvas">
          <svg viewBox="0 0 100 100" role="img" aria-label="Regional pest hotspot map">
            <defs>
              <pattern id="riskHatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <line x1="0" y1="0" x2="0" y2="5" className="ws-hatch-line" />
              </pattern>
              <linearGradient id="districtFill" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#f3f7ee" />
                <stop offset="1" stopColor="#e4ebdd" />
              </linearGradient>
            </defs>

            <path
              d="M8 18 L30 8 L52 14 L68 8 L90 18 L94 38 L86 58 L92 78 L76 92 L52 88 L34 94 L16 82 L6 60 L12 40 Z"
              className="ws-region-outline"
            />
            <path
              d="M30 8 L36 30 L24 48 L34 70 L22 88"
              className="ws-region-line"
              fill="none"
            />
            <path
              d="M68 8 L64 30 L76 48 L70 68 L78 90"
              className="ws-region-line"
              fill="none"
            />
            <path d="M6 56 L92 52" className="ws-region-line" fill="none" />

            <text x="22" y="18" className="ws-region-label">Krishnagiri</text>
            <text x="70" y="18" className="ws-region-label">Dharmapuri</text>
            <text x="50" y="97" className="ws-region-label ws-region-label-center">Salem</text>

            {regions.map((region) => (
              <g key={region.id} className="ws-risk-region">
                <circle
                  cx={region.x}
                  cy={region.y}
                  r={region.band === "insufficient" ? 5 : 7 + region.verified}
                  className={`ws-risk-halo ${riskClass(region.band)}`}
                />
                {region.band === "urgent" || region.band === "high" ? (
                  <circle
                    cx={region.x}
                    cy={region.y}
                    r={7 + region.verified}
                    fill="url(#riskHatch)"
                    className="ws-risk-hatch"
                  />
                ) : null}
                <circle cx={region.x} cy={region.y} r="2" className={`ws-risk-core ${riskClass(region.band)}`} />
                <title>{`${region.district} · ${region.crop} · ${region.pest} · ${region.band} risk · ${region.reports} reports (${region.verified} verified)`}</title>
              </g>
            ))}

            {cases.map((item) => (
              <g key={item.id}>
                <circle
                  cx={item.x}
                  cy={item.y}
                  r={item.verified ? 1.5 : 1.1}
                  className={`ws-case-dot ws-case-${item.verified ? "verified" : "reported"}`}
                  onClick={() => setSelected(item)}
                  role="button"
                  tabIndex={0}
                  aria-label={`${item.pest} in ${item.village}`}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") setSelected(item);
                  }}
                >
                  <title>{`${item.pest} · ${item.village} · ${item.cases} cases`}</title>
                </circle>
              </g>
            ))}
          </svg>

          <div className="ws-map-legend">
            <span><i className="ws-legend-swatch ws-risk-low" /> Low</span>
            <span><i className="ws-legend-swatch ws-risk-moderate" /> Moderate</span>
            <span><i className="ws-legend-swatch ws-risk-high" /> High</span>
            <span><i className="ws-legend-swatch ws-risk-urgent" /> Urgent</span>
            <span><i className="ws-legend-swatch ws-risk-insufficient" /> Insufficient</span>
            <span><i className="ws-legend-dot" /> Case report</span>
          </div>
        </div>

        <div className="ws-hotspot-side">
          {selected ? (
            <div className="ws-case-card">
              <div className="ws-case-card-head">
                <div>
                  <p className="ws-eyebrow">Selected report</p>
                  <h3>{selected.pest}</h3>
                </div>
                <button
                  type="button"
                  className="ws-icon-button"
                  onClick={() => setSelected(null)}
                  aria-label="Clear selection"
                >
                  <Icon name="close" size={16} />
                </button>
              </div>
              <dl className="ws-detail-list">
                <div><dt>Crop</dt><dd>{selected.crop}</dd></div>
                <div><dt>Location</dt><dd>{selected.village}, {selected.district}</dd></div>
                <div><dt>Reported</dt><dd>{formatDate(selected.reportedAt)}</dd></div>
                <div><dt>Cases</dt><dd>{selected.cases}</dd></div>
                <div><dt>Status</dt><dd>{selected.verified ? "Expert verified" : "Awaiting verification"}</dd></div>
              </dl>
              <Badge tone={selected.verified ? "ok" : "warn"}>
                {selected.verified ? "Verified signal" : "Unverified report"}
              </Badge>
              <p className="ws-small ws-muted">
                A verified case is not the same as an area risk score. They are shown as separate layers.
              </p>
            </div>
          ) : (
            <div className="ws-map-aside">
              <div className="ws-panel-head">
                <div>
                  <p className="ws-eyebrow">Predicted risk</p>
                  <h3>Next 48 hours</h3>
                </div>
                <Badge tone="info">Forecast</Badge>
              </div>
              <ul className="ws-rank-list">
                {regions
                  .slice()
                  .sort((a, b) => b.reports - a.reports)
                  .slice(0, 5)
                  .map((region) => (
                    <li key={region.id}>
                      <div>
                        <strong>{region.district}</strong>
                        <span>{region.crop} · {region.pest}</span>
                      </div>
                      <RiskPill band={region.band} />
                    </li>
                  ))}
              </ul>
              <p className="ws-small ws-muted">
                Low risk does not mean the disease is absent. Coverage is shown separately.
              </p>
            </div>
          )}

          <div className="ws-map-aside">
            <div className="ws-panel-head">
              <div>
                <p className="ws-eyebrow">Nearby affected regions</p>
                <h3>Highest case counts</h3>
              </div>
            </div>
            <ul className="ws-rank-list">
              {nearby.map((item) => (
                <li key={item.id}>
                  <div>
                    <strong>{item.village}</strong>
                    <span>{item.pest} · {item.crop}</span>
                  </div>
                  <span className="ws-rank-count">{item.cases}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="ws-coverage-note">
        <Icon name="shield" size={18} />
        <div>
          <strong>Coverage and freshness</strong>
          <p>
            Risk bands are shown only where inputs are fresh. Regions with fewer than 3 verified
            reports show <em>insufficient data</em> rather than a low-risk colour.
          </p>
        </div>
      </div>

      <div className="ws-table-wrap">
        <table className="ws-table">
          <thead>
            <tr>
              <th scope="col">Pest</th>
              <th scope="col">Crop</th>
              <th scope="col">Village</th>
              <th scope="col">District</th>
              <th scope="col">Reported</th>
              <th scope="col">Severity</th>
              <th scope="col">Verification</th>
              <th scope="col">Cases</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((item) => (
              <tr key={item.id}>
                <td><strong>{item.pest}</strong></td>
                <td>{item.crop}</td>
                <td>{item.village}</td>
                <td>{item.district}</td>
                <td>{formatDate(item.reportedAt)}</td>
                <td><Badge tone={severityTone(item.severity) as "low" | "moderate" | "high" | "critical"}>{item.severity}</Badge></td>
                <td>{item.verified ? <Badge tone="ok">Verified</Badge> : <Badge tone="warn">Pending</Badge>}</td>
                <td>{item.cases}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {cases.length === 0 ? <p className="ws-empty-inline">No reports match these filters.</p> : null}
      </div>
    </div>
  );
}

export function HotspotSummary() {
  const { state } = useWorkspace();
  const high = state.riskRegions.filter((region) => region.band === "high" || region.band === "urgent").length;
  const verified = state.cases.filter((item) => item.verified).length;
  return (
    <div className="ws-inline-stats">
      <span><strong>{state.cases.length}</strong> hotspot reports</span>
      <span><strong>{verified}</strong> verified</span>
      <span><strong>{high}</strong> high-risk regions</span>
    </div>
  );
}

export function SeverityFilter({
  value,
  onChange,
}: {
  value: "all" | Severity;
  onChange: (value: "all" | Severity) => void;
}) {
  return (
    <Segmented
      label="Filter severity"
      value={value}
      onChange={onChange}
      options={[
        { value: "all", label: "All" },
        { value: "low", label: "Low" },
        { value: "moderate", label: "Moderate" },
        { value: "high", label: "High" },
        { value: "critical", label: "Critical" },
      ]}
    />
  );
}

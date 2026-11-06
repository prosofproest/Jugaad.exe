"use client";

import { HotspotMap } from "@/components/workspace/hotspot-map";
import { Badge, Icon, PageHeader, ProgressBar, RiskPill, StatCard } from "@/components/workspace/ui";
import { formatDateTime } from "@/lib/format";
import { useWorkspace } from "@/lib/workspace/store";

export default function HotspotsPage() {
  const { state } = useWorkspace();
  const highRisk = state.riskRegions.filter((region) => region.band === "high" || region.band === "urgent");
  const verified = state.cases.filter((item) => item.verified);
  const coverageGood = state.riskRegions.filter((region) => region.coverage === "good").length;

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Pest hotspot map"
        title="Regional spread, verified cases and predicted risk"
        lede="Separate layers for reported cases, expert-verified cases and the area outlook. A verified case never becomes a risk band, and a risk band never verifies a case."
        actions={
          <div className="ws-chip-row">
            <Badge tone="info">Updated 6 Nov, 05:00</Badge>
            <Badge tone="neutral">Forecast horizon 6–8 Nov</Badge>
          </div>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Reported cases" value={state.cases.reduce((sum, item) => sum + item.cases, 0)} detail={`${state.cases.length} hotspot clusters`} icon="hotspot" tone="brand" />
        <StatCard label="Expert verified" value={verified.reduce((sum, item) => sum + item.cases, 0)} detail={`${verified.length} verified clusters`} icon="shield" tone="ok" />
        <StatCard label="High-risk regions" value={highRisk.length} detail={highRisk.map((region) => region.district).join(", ")} icon="alert" tone="bad" />
        <StatCard label="Good coverage" value={`${coverageGood}/${state.riskRegions.length}`} detail="Regions with enough verified reports" icon="map" tone="warn" />
      </div>

      <HotspotMap />

      <div className="ws-two-col">
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div><p className="ws-eyebrow">Predicted pest risk</p><h2>Area outlooks</h2></div>
            <Badge tone="info">Not an outbreak alert</Badge>
          </div>
          <div className="ws-risk-list">
            {state.riskRegions.map((region) => (
              <div key={region.id} className="ws-risk-row">
                <div className="ws-risk-row-main">
                  <div><strong>{region.district} · {region.crop}</strong><span className="ws-small ws-muted">{region.pest}</span></div>
                  <RiskPill band={region.band} />
                </div>
                <div className="ws-risk-row-meta">
                  <span>{region.reports} reports · {region.verified} verified</span>
                  <span>Coverage: {region.coverage}</span>
                  <span>Valid {region.horizon}</span>
                </div>
                <ProgressBar value={Math.min(100, region.reports * 9)} label="Data coverage signal" tone={region.band === "insufficient" ? "warn" : "brand"} />
              </div>
            ))}
          </div>
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">Regional reports</p><h2>Latest verified activity</h2></div><Badge tone="neutral">{verified.length}</Badge></div>
          <ul className="ws-activity-list">
            {verified.map((item) => (
              <li key={item.id}>
                <span className="ws-activity-dot ws-tone-bad" />
                <div>
                  <strong>{item.pest}</strong>
                  <span className="ws-small ws-muted">{item.village}, {item.district} · {item.cases} cases · {formatDateTime(item.reportedAt)}</span>
                </div>
                <Badge tone="ok">Verified</Badge>
              </li>
            ))}
          </ul>
          <div className="ws-notice">
            <Icon name="shield" size={17} />
            <p>Low risk does not mean the disease is absent. Coverage and freshness are shown next to every outlook.</p>
          </div>
        </section>
      </div>
    </div>
  );
}

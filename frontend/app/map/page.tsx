"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { FarmMap, LAYERS, type FarmLayer } from "@/components/workspace/farm-map";
import {
  Badge,
  HealthPill,
  Icon,
  PageHeader,
  ProgressBar,
  StatCard,
  Tabs,
} from "@/components/workspace/ui";
import { formatDate } from "@/lib/format";
import { cropGroupHealth, healthLabel, useWorkspace } from "@/lib/workspace/store";
import type { Health } from "@/lib/workspace/types";

type View = "current" | "crops" | "plants" | "recovery" | "history";

export default function FarmHealthMapPage() {
  const { state } = useWorkspace();
  const [farmId, setFarmId] = useState(state.farms[0]?.id ?? "");
  const [layer, setLayer] = useState<FarmLayer>("health");
  const [view, setView] = useState<View>("current");
  const [plantFilter, setPlantFilter] = useState("all");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const farm = params.get("farm");
    if (farm && state.farms.some((item) => item.id === farm)) setFarmId(farm);
  }, [state.farms]);

  const farm = state.farms.find((item) => item.id === farmId) ?? state.farms[0];
  const plots = state.plots.filter((plot) => plot.farmId === farm?.id);
  const groups = state.cropGroups.filter((group) => group.farmId === farm?.id);
  const plants = state.plants.filter((plant) => plant.farmId === farm?.id);
  const analyses = state.analyses.filter((analysis) => analysis.farmId === farm?.id);
  const inspections = state.inspections.filter((inspection) => inspection.farmId === farm?.id);

  const healthCounts = useMemo(() => {
    const counts: Record<Health, number> = { healthy: 0, watch: 0, pest: 0, diseased: 0, recovering: 0 };
    for (const plant of plants) counts[plant.health] += 1;
    return counts;
  }, [plants]);

  const affectedPlots = plots.filter((plot) => plot.health === "pest" || plot.health === "diseased");
  const recovering = inspections.filter((inspection) => (inspection.recovery ?? 0) > 0);
  const filteredPlants = plantFilter === "all" ? plants : plants.filter((plant) => plant.cropGroupId === plantFilter);

  if (!farm) {
    return (
      <div className="ws-page">
        <PageHeader eyebrow="Farm health map" title="No farm registered" lede="Add a farm to unlock the health map." />
        <Link href="/farms" className="ws-button ws-button-primary">Add a farm</Link>
      </div>
    );
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Farm health map"
        title="Every plot, crop group and plant on one map"
        lede="Switch between health, pest, disease, severity, recovery and historical layers. Colour is always paired with a label and pattern."
        actions={
          <label className="ws-select-inline">
            <span>Farm</span>
            <select value={farm.id} onChange={(event) => setFarmId(event.target.value)}>
              {state.farms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Total plots" value={plots.length} detail={`${plots.reduce((sum, plot) => sum + plot.sections.length, 0)} sections`} icon="map" tone="brand" />
        <StatCard label="Affected areas" value={affectedPlots.length} detail={affectedPlots.map((plot) => plot.name).join(", ") || "None"} icon="alert" tone={affectedPlots.length > 0 ? "bad" : "ok"} />
        <StatCard label="Plants healthy" value={healthCounts.healthy} detail={`${plants.length} plants tracked`} icon="plant" tone="ok" />
        <StatCard label="Recovering" value={healthCounts.recovering} detail="Follow-up in progress" icon="monitoring" tone="ok" />
      </div>

      <Tabs
        label="Map views"
        value={view}
        onChange={setView}
        tabs={[
          { value: "current", label: "Farm map" },
          { value: "crops", label: "Crop health" },
          { value: "plants", label: "Plant indicators" },
          { value: "recovery", label: "Recovery" },
          { value: "history", label: "History" },
        ]}
      />

      {view === "current" ? (
        <div className="ws-map-layout">
          <section className="ws-panel">
            <div className="ws-panel-head">
              <div><p className="ws-eyebrow">{farm.village} · {farm.district}</p><h2>{farm.name}</h2></div>
              <div className="ws-chip-row">
                <Badge tone="info">GPS boundary</Badge>
                <Badge tone="neutral">{farm.areaAcres} acres</Badge>
              </div>
            </div>
            <FarmMap farm={farm} layer={layer} onLayerChange={setLayer} showPlants />
          </section>
          <aside className="ws-stack">
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Layer</h2><Badge tone="neutral">{LAYERS.find((item) => item.value === layer)?.label}</Badge></div>
              <div className="ws-layer-list">
                {LAYERS.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    className={layer === item.value ? "ws-layer-option ws-layer-option-active" : "ws-layer-option"}
                    onClick={() => setLayer(item.value)}
                  >
                    <strong>{item.label}</strong>
                    <small>{item.hint}</small>
                  </button>
                ))}
              </div>
            </section>
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Plant distribution</h2></div>
              <ul className="ws-distribution">
                {(Object.keys(healthCounts) as Health[]).map((health) => (
                  <li key={health}>
                    <span className={`ws-legend-swatch ws-health-${health}`} />
                    <span>{healthLabel(health)}</span>
                    <strong>{healthCounts[health]}</strong>
                  </li>
                ))}
              </ul>
            </section>
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Plot summary</h2></div>
              <ul className="ws-rank-list">
                {plots.map((plot) => (
                  <li key={plot.id}>
                    <div><strong>{plot.name}</strong><span>{plot.areaAcres} acres · {plot.sections.length} sections</span></div>
                    <HealthPill health={plot.health} />
                  </li>
                ))}
              </ul>
            </section>
          </aside>
        </div>
      ) : null}

      {view === "crops" ? (
        <div className="ws-page">
          <div className="ws-banner ws-banner-info">
            <Icon name="leaf" size={18} />
            <div><strong>Crop-wise health map</strong><p>Each crop group is assessed from its plants and its latest observations, not from a single photo.</p></div>
          </div>
          <div className="ws-crop-map-grid">
            {groups.map((group) => {
              const groupPlants = plants.filter((plant) => plant.cropGroupId === group.id);
              const healthy = groupPlants.filter((plant) => plant.health === "healthy").length;
              const health = cropGroupHealth(state, group.id);
              return (
                <article key={group.id} className="ws-crop-map-card">
                  <div className="ws-crop-map-head">
                    <div><p className="ws-eyebrow">{group.crop}</p><h3>{group.name}</h3></div>
                    <HealthPill health={health} />
                  </div>
                  <div className={`ws-crop-map-canvas ws-health-${health}`}>
                    {groupPlants.map((plant) => (
                      <span key={plant.id} className={`ws-plant-dot ws-health-${plant.health}`} title={`${plant.code}: ${healthLabel(plant.health)}`} />
                    ))}
                    {groupPlants.length === 0 ? <span className="ws-small">No individual plants registered</span> : null}
                  </div>
                  <div className="ws-crop-map-meta">
                    <span>{groupPlants.length} plants</span>
                    <span>{group.variety} · {group.stage}</span>
                  </div>
                  <ProgressBar value={groupPlants.length > 0 ? Math.round((healthy / groupPlants.length) * 100) : 100} label="Healthy plants" tone={health === "healthy" ? "ok" : health === "watch" ? "warn" : "bad"} />
                </article>
              );
            })}
          </div>
        </div>
      ) : null}

      {view === "plants" ? (
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div><p className="ws-eyebrow">Plant-wise indicators</p><h2>Individual plant health</h2></div>
            <select value={plantFilter} onChange={(event) => setPlantFilter(event.target.value)} aria-label="Filter by crop group">
              <option value="all">All crop groups</option>
              {groups.map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}
            </select>
          </div>
          <div className="ws-plant-grid">
            {filteredPlants.map((plant) => (
              <div key={plant.id} className="ws-plant-card">
                <span className={`ws-plant-indicator ws-health-${plant.health}`} />
                <div>
                  <strong>{plant.code}</strong>
                  <span className="ws-small ws-muted">{plant.label}</span>
                  <span className="ws-small ws-muted">Last scouted {formatDate(plant.lastScouted)}</span>
                </div>
                <HealthPill health={plant.health} />
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {view === "recovery" ? (
        <div className="ws-two-col">
          <section className="ws-panel">
            <div className="ws-panel-head"><div><p className="ws-eyebrow">Recovery progress</p><h2>Treatment follow-ups</h2></div></div>
            {recovering.length > 0 ? (
              <ul className="ws-recovery-list">
                {recovering.map((inspection) => (
                  <li key={inspection.id}>
                    <div className="ws-recovery-head">
                      <div><strong>{inspection.title}</strong><span className="ws-small ws-muted">{inspection.target}</span></div>
                      <Badge tone={inspection.failedTreatment ? "bad" : "ok"}>{inspection.failedTreatment ? "Treatment needs review" : "Recovering"}</Badge>
                    </div>
                    <ProgressBar value={inspection.recovery ?? 0} label="Plant recovery" tone={(inspection.recovery ?? 0) > 60 ? "ok" : "warn"} />
                    <ProgressBar value={inspection.effectiveness ?? 0} label="Treatment effectiveness" tone="brand" />
                    <div className="ws-compare-strip ws-compare-small">
                      <div><span className="ws-photo ws-photo-sm ws-tone-5" /><span className="ws-small">Before</span></div>
                      <Icon name="arrow" size={18} />
                      <div><span className="ws-photo ws-photo-sm ws-tone-3" /><span className="ws-small">After</span></div>
                      <p className="ws-small ws-muted">{inspection.notes}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="ws-empty-inline">No recovery follow-ups recorded yet.</p>
            )}
          </section>
          <section className="ws-panel">
            <div className="ws-panel-head"><h2>Recovery map</h2><Badge tone="info">Layer</Badge></div>
            <FarmMap farm={farm} layer="recovery" showPlants />
            <p className="ws-small ws-muted ws-mt">
              Dotted plots are recovering after treatment. Recovery is a field judgement, not a model prediction.
            </p>
          </section>
        </div>
      ) : null}

      {view === "history" ? (
        <div className="ws-two-col">
          <section className="ws-panel">
            <div className="ws-panel-head"><div><p className="ws-eyebrow">Historical infestation</p><h2>Observations over time</h2></div><Badge tone="neutral">{analyses.length} records</Badge></div>
            <ul className="ws-timeline">
              {analyses.slice().sort((a, b) => b.createdAt.localeCompare(a.createdAt)).map((analysis) => (
                <li key={analysis.id}>
                  <span className={`ws-timeline-dot ws-tone-${analysis.severity === "critical" || analysis.severity === "high" ? "bad" : "warn"}`} />
                  <div className="ws-timeline-body">
                    <div><strong>{analysis.subjectLabel}</strong><span className="ws-small ws-muted">{formatDate(analysis.createdAt)}</span></div>
                    <span className="ws-small">Possible {analysis.pest ?? analysis.disease} · {analysis.severity} severity</span>
                  </div>
                  <Link href={`/analysis?focus=${analysis.id}`} className="ws-link">Open</Link>
                </li>
              ))}
            </ul>
          </section>
          <section className="ws-panel">
            <div className="ws-panel-head"><h2>Historical map</h2><Badge tone="neutral">All time</Badge></div>
            <FarmMap farm={farm} layer="history" showPlants />
            <p className="ws-small ws-muted ws-mt">Use the analysis list to open the original evidence and its expert review state.</p>
          </section>
        </div>
      ) : null}
    </div>
  );
}

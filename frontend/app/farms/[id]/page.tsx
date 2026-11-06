"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { FarmMap, type FarmLayer } from "@/components/workspace/farm-map";
import {
  Badge,
  Field,
  HealthPill,
  Icon,
  Modal,
  PageHeader,
  ProgressBar,
  StatCard,
  Tabs,
} from "@/components/workspace/ui";
import { formatAcres, formatDate } from "@/lib/format";
import { cropGroupHealth, healthLabel, useWorkspace } from "@/lib/workspace/store";
import type { Health } from "@/lib/workspace/types";

type Tab = "overview" | "plots" | "crops" | "plants" | "activity";

const HEALTH_OPTIONS: Health[] = ["healthy", "watch", "pest", "diseased", "recovering"];

export default function FarmDetailPage() {
  const params = useParams<{ id: string }>();
  const { state, addPlot, addCropGroup, addPlant, updatePlant } = useWorkspace();
  const [tab, setTab] = useState<Tab>("overview");
  const [layer, setLayer] = useState<FarmLayer>("health");
  const [plotOpen, setPlotOpen] = useState(false);
  const [cropOpen, setCropOpen] = useState(false);
  const [plantOpen, setPlantOpen] = useState(false);
  const [plantFilter, setPlantFilter] = useState("all");

  const farm = state.farms.find((item) => item.id === params.id);
  const plots = useMemo(() => state.plots.filter((plot) => plot.farmId === params.id), [state.plots, params.id]);
  const groups = useMemo(
    () => state.cropGroups.filter((group) => group.farmId === params.id),
    [state.cropGroups, params.id],
  );
  const plants = useMemo(
    () => state.plants.filter((plant) => plant.farmId === params.id),
    [state.plants, params.id],
  );
  const analyses = state.analyses.filter((analysis) => analysis.farmId === params.id);
  const inspections = state.inspections.filter((inspection) => inspection.farmId === params.id);

  const [plotForm, setPlotForm] = useState({ name: "", area: "1" });
  const [cropForm, setCropForm] = useState({
    plotId: plots[0]?.id ?? "",
    sectionId: "",
    crop: "Tomato",
    variety: "",
    area: "1",
  });
  const [plantForm, setPlantForm] = useState({
    plotId: plots[0]?.id ?? "",
    cropGroupId: groups[0]?.id ?? "",
    label: "",
  });

  if (!farm) {
    return (
      <div className="ws-page">
        <PageHeader eyebrow="Farm management" title="Farm not found" lede="This farm may have been removed from the demo workspace." />
        <Link href="/farms" className="ws-button ws-button-primary">Back to farms</Link>
      </div>
    );
  }

  const healthy = plants.filter((plant) => plant.health === "healthy").length;
  const affected = plants.filter((plant) => plant.health === "pest" || plant.health === "diseased").length;
  const scouting = inspections.filter((item) => item.status === "scheduled" || item.status === "in_progress");
  const visiblePlants = plantFilter === "all" ? plants : plants.filter((plant) => plant.cropGroupId === plantFilter);
  const plotGroups = (plotId: string) => groups.filter((group) => group.plotId === plotId);
  const sectionsOfPlot = state.plots.find((plot) => plot.id === cropForm.plotId)?.sections ?? [];

  function submitPlot(event: React.FormEvent) {
    event.preventDefault();
    if (!plotForm.name.trim()) return;
    addPlot(params.id, plotForm.name.trim(), Number(plotForm.area) || 1);
    setPlotForm({ name: "", area: "1" });
    setPlotOpen(false);
  }

  function submitCrop(event: React.FormEvent) {
    event.preventDefault();
    if (!cropForm.plotId) return;
    addCropGroup(
      params.id,
      cropForm.plotId,
      cropForm.sectionId || null,
      cropForm.crop,
      cropForm.variety || "Local",
      Number(cropForm.area) || 1,
    );
    setCropOpen(false);
  }

  function submitPlant(event: React.FormEvent) {
    event.preventDefault();
    if (!plantForm.cropGroupId) return;
    addPlant(params.id, plantForm.plotId, plantForm.cropGroupId, plantForm.label);
    setPlantOpen(false);
    setPlantForm((current) => ({ ...current, label: "" }));
  }

  return (
    <div className="ws-page">
      <nav className="ws-breadcrumb" aria-label="Breadcrumb">
        <Link href="/farms">Farms</Link>
        <span>/</span>
        <span>{farm.name}</span>
      </nav>

      <PageHeader
        eyebrow={`${farm.village} · ${farm.district} · ${farm.state}`}
        title={farm.name}
        lede={`${formatAcres(farm.areaAcres)} · ${farm.soil} soil · ${farm.irrigation}. GPS ${farm.lat.toFixed(5)}, ${farm.lng.toFixed(5)}.`}
        actions={
          <>
            <button type="button" className="ws-button ws-button-secondary" onClick={() => setPlotOpen(true)}>
              <Icon name="plus" size={16} /> Add plot
            </button>
            <button type="button" className="ws-button ws-button-primary" onClick={() => setCropOpen(true)}>
              <Icon name="leaf" size={16} /> Add crop group
            </button>
          </>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Healthy plants" value={`${healthy}/${plants.length}`} detail={`${plants.length > 0 ? Math.round((healthy / plants.length) * 100) : 0}% of tracked plants`} icon="plant" tone="ok" />
        <StatCard label="Affected plants" value={affected} detail="Pest or disease signs" icon="alert" tone={affected > 0 ? "bad" : "default"} />
        <StatCard label="Crop groups" value={groups.length} detail={`${new Set(groups.map((group) => group.crop)).size} crop types`} icon="leaf" />
        <StatCard label="Next scouting" value={scouting[0] ? formatDate(scouting[0].scheduledFor) : "Not set"} detail={scouting[0]?.title ?? "Schedule an inspection"} icon="calendar" tone="warn" />
      </div>

      <Tabs
        label="Farm sections"
        value={tab}
        onChange={setTab}
        tabs={[
          { value: "overview", label: "Overview" },
          { value: "plots", label: "Plots & sections", count: plots.length },
          { value: "crops", label: "Crop groups", count: groups.length },
          { value: "plants", label: "Plants", count: plants.length },
          { value: "activity", label: "Activity", count: analyses.length },
        ]}
      />

      {tab === "overview" ? (
        <div className="ws-two-col ws-two-col-wide">
          <section className="ws-panel">
            <div className="ws-panel-head">
              <div>
                <p className="ws-eyebrow">Farm health map</p>
                <h2>Plot and plant status</h2>
              </div>
              <Link href={`/map?farm=${farm.id}`} className="ws-link">Open full map <Icon name="arrow" size={14} /></Link>
            </div>
            <FarmMap farm={farm} layer={layer} onLayerChange={setLayer} showPlants />
          </section>
          <div className="ws-stack">
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Recent observations</h2><Badge tone="neutral">{analyses.length}</Badge></div>
              <ul className="ws-activity-list">
                {analyses.slice(0, 4).map((analysis) => (
                  <li key={analysis.id}>
                    <span className={`ws-activity-dot ws-tone-${analysis.severity === "critical" || analysis.severity === "high" ? "bad" : "warn"}`} />
                    <div>
                      <strong>{analysis.subjectLabel}</strong>
                      <span className="ws-small ws-muted">Possible {analysis.pest ?? analysis.disease} · {formatDate(analysis.createdAt)}</span>
                    </div>
                    <Badge tone="neutral">{analysis.reviewStatus.replace("_", " ")}</Badge>
                  </li>
                ))}
              </ul>
            </section>
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Farm details</h2></div>
              <dl className="ws-detail-list">
                <div><dt>Registered</dt><dd>{formatDate(farm.createdAt)}</dd></div>
                <div><dt>Area</dt><dd>{formatAcres(farm.areaAcres)}</dd></div>
                <div><dt>Soil</dt><dd>{farm.soil}</dd></div>
                <div><dt>Irrigation</dt><dd>{farm.irrigation}</dd></div>
                <div><dt>GPS</dt><dd>{farm.lat.toFixed(5)}, {farm.lng.toFixed(5)}</dd></div>
              </dl>
            </section>
          </div>
        </div>
      ) : null}

      {tab === "plots" ? (
        <div className="ws-page">
          <div className="ws-toolbar">
            <p className="ws-muted ws-small">Every plot can be divided into sections and each section assigned to a crop group.</p>
            <button type="button" className="ws-button ws-button-secondary" onClick={() => setPlotOpen(true)}>
              <Icon name="plus" size={16} /> Add plot
            </button>
          </div>
          <div className="ws-plot-grid">
            {plots.map((plot) => {
              const groupsInPlot = plotGroups(plot.id);
              return (
                <article key={plot.id} className="ws-plot-card">
                  <div className="ws-plot-head">
                    <div>
                      <p className="ws-eyebrow">Plot</p>
                      <h2>{plot.name}</h2>
                      <span className="ws-small ws-muted">{formatAcres(plot.areaAcres)}</span>
                    </div>
                    <HealthPill health={plot.health} />
                  </div>
                  <div className="ws-section-list">
                    {plot.sections.map((section) => {
                      const group = groups.find((item) => item.id === section.cropGroupId);
                      return (
                        <div key={section.id} className="ws-section-row">
                          <div className="ws-section-icon"><Icon name="map" size={15} /></div>
                          <div>
                            <strong>{section.name}</strong>
                            <span className="ws-small ws-muted">
                              {section.areaAcres} acres · {group ? `${group.crop} (${group.variety})` : "No crop assigned"}
                            </span>
                            {section.subSections && section.subSections.length > 0 ? (
                              <div className="ws-chip-row ws-mt-sm">
                                {section.subSections.map((sub) => <span key={sub} className="ws-chip ws-chip-muted">{sub}</span>)}
                              </div>
                            ) : null}
                          </div>
                          {group ? <HealthPill health={cropGroupHealth(state, group.id)} /> : <Badge tone="neutral">Unassigned</Badge>}
                        </div>
                      );
                    })}
                  </div>
                  <div className="ws-chip-row">
                    {groupsInPlot.map((group) => (
                      <span key={group.id} className="ws-chip">{group.crop} · {group.stage}</span>
                    ))}
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      ) : null}

      {tab === "crops" ? (
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div><p className="ws-eyebrow">Crop groups</p><h2>Registered crops in this farm</h2></div>
            <button type="button" className="ws-button ws-button-secondary" onClick={() => setCropOpen(true)}>
              <Icon name="plus" size={16} /> Add crop group
            </button>
          </div>
          <div className="ws-table-wrap">
            <table className="ws-table">
              <thead>
                <tr>
                  <th>Crop group</th><th>Crop / variety</th><th>Plot</th><th>Stage</th><th>Planted</th><th>Area</th><th>Plants</th><th>Health</th>
                </tr>
              </thead>
              <tbody>
                {groups.map((group) => {
                  const groupPlants = plants.filter((plant) => plant.cropGroupId === group.id);
                  return (
                    <tr key={group.id}>
                      <td><strong>{group.name}</strong></td>
                      <td>{group.crop} · {group.variety}</td>
                      <td>{plots.find((plot) => plot.id === group.plotId)?.name}</td>
                      <td>{group.stage}</td>
                      <td>{formatDate(group.plantedOn)}</td>
                      <td>{group.areaAcres} ac</td>
                      <td>{groupPlants.length}</td>
                      <td><HealthPill health={cropGroupHealth(state, group.id)} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {tab === "plants" ? (
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div><p className="ws-eyebrow">Individual plants</p><h2>Plant registry</h2></div>
            <div className="ws-row">
              <select value={plantFilter} onChange={(event) => setPlantFilter(event.target.value)} aria-label="Filter by crop group">
                <option value="all">All crop groups</option>
                {groups.map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}
              </select>
              <button type="button" className="ws-button ws-button-secondary" onClick={() => setPlantOpen(true)}>
                <Icon name="plus" size={16} /> Register plant
              </button>
            </div>
          </div>
          <p className="ws-small ws-muted">Each plant receives a unique ID and its own health history. Update health after scouting.</p>
          <div className="ws-table-wrap">
            <table className="ws-table">
              <thead>
                <tr><th>Unique ID</th><th>Label</th><th>Crop group</th><th>Planted</th><th>Last scouted</th><th>Health</th><th>Notes</th></tr>
              </thead>
              <tbody>
                {visiblePlants.map((plant) => (
                  <tr key={plant.id}>
                    <td><span className="ws-mono">{plant.code}</span></td>
                    <td>{plant.label}</td>
                    <td>{groups.find((group) => group.id === plant.cropGroupId)?.name}</td>
                    <td>{formatDate(plant.plantedOn)}</td>
                    <td>{formatDate(plant.lastScouted)}</td>
                    <td>
                      <select
                        value={plant.health}
                        aria-label={`Health for ${plant.code}`}
                        onChange={(event) =>
                          updatePlant(plant.id, {
                            health: event.target.value as Health,
                            lastScouted: new Date().toISOString().slice(0, 10),
                          })
                        }
                      >
                        {HEALTH_OPTIONS.map((health) => <option key={health} value={health}>{healthLabel(health)}</option>)}
                      </select>
                    </td>
                    <td className="ws-small ws-muted">{plant.notes || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {visiblePlants.length === 0 ? <p className="ws-empty-inline">No plants registered for this crop group yet.</p> : null}
        </section>
      ) : null}

      {tab === "activity" ? (
        <div className="ws-two-col">
          <section className="ws-panel">
            <div className="ws-panel-head"><h2>AI analyses</h2><Badge tone="neutral">{analyses.length}</Badge></div>
            <ul className="ws-activity-list">
              {analyses.map((analysis) => (
                <li key={analysis.id}>
                  <span className={`ws-activity-dot ws-tone-${analysis.severity === "critical" ? "bad" : "warn"}`} />
                  <div>
                    <strong>{analysis.subjectLabel}</strong>
                    <span className="ws-small ws-muted">{analysis.pest ?? analysis.disease} · {formatDate(analysis.createdAt)}</span>
                  </div>
                  <Link href={`/analysis?focus=${analysis.id}`} className="ws-link">Open</Link>
                </li>
              ))}
            </ul>
          </section>
          <section className="ws-panel">
            <div className="ws-panel-head"><h2>Monitoring</h2><Link href="/monitoring" className="ws-link">All visits</Link></div>
            <ul className="ws-activity-list">
              {inspections.map((inspection) => (
                <li key={inspection.id}>
                  <span className="ws-activity-dot ws-tone-warn" />
                  <div><strong>{inspection.title}</strong><span className="ws-small ws-muted">{formatDate(inspection.scheduledFor)} · {inspection.status}</span></div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      ) : null}

      <Modal
        open={plotOpen}
        onClose={() => setPlotOpen(false)}
        title="Add a plot"
        footer={
          <>
            <button type="button" className="ws-button ws-button-ghost" onClick={() => setPlotOpen(false)}>Cancel</button>
            <button type="submit" form="plot-form" className="ws-button ws-button-primary">Add plot</button>
          </>
        }
      >
        <form id="plot-form" onSubmit={submitPlot} className="ws-form">
          <Field label="Plot name"><input value={plotForm.name} onChange={(event) => setPlotForm({ ...plotForm, name: event.target.value })} placeholder="East Plot" required /></Field>
          <Field label="Area (acres)"><input type="number" min="0.1" step="0.1" value={plotForm.area} onChange={(event) => setPlotForm({ ...plotForm, area: event.target.value })} /></Field>
          <p className="ws-small ws-muted">A first section is created automatically. You can map sections to crop groups next.</p>
        </form>
      </Modal>

      <Modal
        open={cropOpen}
        onClose={() => setCropOpen(false)}
        title="Add a crop group"
        footer={
          <>
            <button type="button" className="ws-button ws-button-ghost" onClick={() => setCropOpen(false)}>Cancel</button>
            <button type="submit" form="crop-form" className="ws-button ws-button-primary">Add crop group</button>
          </>
        }
      >
        <form id="crop-form" onSubmit={submitCrop} className="ws-form">
          <div className="ws-form-grid">
            <Field label="Plot">
              <select
                value={cropForm.plotId}
                onChange={(event) => {
                  const plot = plots.find((item) => item.id === event.target.value);
                  setCropForm({ ...cropForm, plotId: event.target.value, sectionId: plot?.sections[0]?.id ?? "" });
                }}
              >
                {plots.map((plot) => <option key={plot.id} value={plot.id}>{plot.name}</option>)}
              </select>
            </Field>
            <Field label="Section">
              <select value={cropForm.sectionId} onChange={(event) => setCropForm({ ...cropForm, sectionId: event.target.value })}>
                <option value="">Unassigned</option>
                {sectionsOfPlot.map((section) => <option key={section.id} value={section.id}>{section.name}</option>)}
              </select>
            </Field>
          </div>
          <div className="ws-form-grid">
            <Field label="Crop">
              <select value={cropForm.crop} onChange={(event) => setCropForm({ ...cropForm, crop: event.target.value })}>
                <option>Tomato</option><option>Chilli</option><option>Brinjal</option><option>Mango</option><option>Maize</option><option>Cowpea</option><option>Beans</option>
              </select>
            </Field>
            <Field label="Variety"><input value={cropForm.variety} onChange={(event) => setCropForm({ ...cropForm, variety: event.target.value })} placeholder="Arka Rakshak" /></Field>
          </div>
          <Field label="Area (acres)"><input type="number" min="0.1" step="0.1" value={cropForm.area} onChange={(event) => setCropForm({ ...cropForm, area: event.target.value })} /></Field>
        </form>
      </Modal>

      <Modal
        open={plantOpen}
        onClose={() => setPlantOpen(false)}
        title="Register an individual plant"
        footer={
          <>
            <button type="button" className="ws-button ws-button-ghost" onClick={() => setPlantOpen(false)}>Cancel</button>
            <button type="submit" form="plant-form" className="ws-button ws-button-primary">Register plant</button>
          </>
        }
      >
        <form id="plant-form" onSubmit={submitPlant} className="ws-form">
          <Field label="Crop group">
            <select
              value={plantForm.cropGroupId}
              onChange={(event) => {
                const group = groups.find((item) => item.id === event.target.value);
                setPlantForm({ ...plantForm, cropGroupId: event.target.value, plotId: group?.plotId ?? plantForm.plotId });
              }}
            >
              {groups.map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}
            </select>
          </Field>
          <Field label="Plant label" hint="A unique ID is generated automatically from the crop and sequence.">
            <input value={plantForm.label} onChange={(event) => setPlantForm({ ...plantForm, label: event.target.value })} placeholder="Tomato row 3 plant 1" />
          </Field>
        </form>
      </Modal>
    </div>
  );
}

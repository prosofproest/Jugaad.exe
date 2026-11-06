"use client";

import Link from "next/link";
import { useState } from "react";

import {
  Badge,
  EmptyState,
  Field,
  HealthPill,
  Icon,
  Modal,
  PageHeader,
  PhotoTile,
  ProgressBar,
  SeverityPill,
  StatCard,
  Tabs,
} from "@/components/workspace/ui";
import { formatDate, formatDateTime } from "@/lib/format";
import { useWorkspace } from "@/lib/workspace/store";
import type { Analysis } from "@/lib/workspace/types";

type Tab = "queue" | "inspections" | "regional";

export default function ExpertPage() {
  const { state, role, setRole, resolveReview, updateInspection } = useWorkspace();
  const [tab, setTab] = useState<Tab>("queue");
  const [active, setActive] = useState<Analysis | null>(null);
  const [verdict, setVerdict] = useState<"verified" | "corrected" | "rejected">("verified");
  const [correctedLabel, setCorrectedLabel] = useState("");
  const [note, setNote] = useState("");
  const [recommendations, setRecommendations] = useState("");
  const [photoFor, setPhotoFor] = useState<string | null>(null);

  if (role === "farmer") {
    return (
      <div className="ws-page">
        <PageHeader eyebrow="Expert desk" title="Restricted workspace" lede="The expert and field-agent desk is available to verification roles. Switch to the demo expert or agent role to explore it." />
        <div className="ws-locked">
          <Icon name="shield" size={26} />
          <h2>Verification permission required</h2>
          <p className="ws-muted">
            Farmers can request expert review from an assessment, but cannot verify or correct a
            diagnosis. This separation protects the audit trail.
          </p>
          <div className="ws-row">
            <button type="button" className="ws-button ws-button-primary" onClick={() => setRole("expert")}>Open demo expert desk</button>
            <Link href="/analysis" className="ws-button ws-button-secondary">Back to analyses</Link>
          </div>
        </div>
      </div>
    );
  }

  const pending = state.analyses.filter((analysis) => analysis.reviewStatus === "pending");
  const verified = state.analyses.filter((analysis) => analysis.reviewStatus === "verified" || analysis.reviewStatus === "corrected");
  const inspections = state.inspections.filter((inspection) => inspection.status === "scheduled" || inspection.status === "in_progress" || inspection.status === "overdue");
  const verifiedCases = state.cases.filter((item) => item.verified);

  function openReview(analysis: Analysis) {
    setActive(analysis);
    setVerdict("verified");
    setCorrectedLabel(analysis.disease ?? analysis.pest ?? "");
    setNote("");
    setRecommendations("");
  }

  function submitReview(event: React.FormEvent) {
    event.preventDefault();
    if (!active) return;
    resolveReview(active.id, {
      verdict,
      correctedLabel: verdict === "corrected" ? correctedLabel : undefined,
      note: note || "Reviewed against field evidence and farmer notes.",
      recommendations: recommendations
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean),
    });
    setActive(null);
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Expert & field agent desk"
        title="Verify, correct and advise"
        lede="A triageable queue with farmer reports, pending verification, field inspections and regional evidence. Corrections are recorded, never overwritten silently."
        actions={
          <div className="ws-chip-row">
            <Badge tone="purple">{pending.length} pending</Badge>
            <Badge tone="ok">{verified.length} reviewed</Badge>
          </div>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Pending verification" value={pending.length} detail="Oldest request 18 hours" icon="expert" tone="warn" />
        <StatCard label="Field inspections" value={inspections.length} detail={`${inspections.filter((item) => item.status === "overdue").length} overdue`} icon="monitoring" tone="bad" />
        <StatCard label="Reviewed this week" value={verified.length} detail="Verified or corrected" icon="shield" tone="ok" />
        <StatCard label="Regional cases" value={state.cases.length} detail={`${verifiedCases.length} expert verified`} icon="hotspot" tone="brand" />
      </div>

      <Tabs
        label="Expert desk views"
        value={tab}
        onChange={setTab}
        tabs={[
          { value: "queue", label: "Verification queue", count: pending.length },
          { value: "inspections", label: "Assigned inspections", count: inspections.length },
          { value: "regional", label: "Regional reports", count: state.cases.length },
        ]}
      />

      {tab === "queue" ? (
        <div className="ws-expert-grid">
          <section className="ws-panel">
            <div className="ws-panel-head">
              <div><p className="ws-eyebrow">Farmer-submitted reports</p><h2>Pending verification</h2></div>
              <Badge tone="neutral">Sorted by urgency</Badge>
            </div>
            <ul className="ws-queue-cards">
              {pending.map((analysis) => (
                <li key={analysis.id} className="ws-queue-card">
                  <PhotoTile tone={analysis.imageTone} mediaType={analysis.mediaType} label={analysis.subjectLabel} size="md" />
                  <div className="ws-queue-card-body">
                    <div className="ws-queue-card-top">
                      <div>
                        <strong>{analysis.subjectLabel}</strong>
                        <span className="ws-small ws-muted">{analysis.farmName} · {formatDateTime(analysis.createdAt)}</span>
                      </div>
                      <div className="ws-chip-row">
                        <SeverityPill severity={analysis.severity} />
                        <Badge tone="warn">Awaiting review</Badge>
                      </div>
                    </div>
                    <p className="ws-small">
                      <strong>Possible match:</strong> {analysis.pest ?? analysis.disease} · {analysis.confidenceBand} confidence · not calibrated
                    </p>
                    <p className="ws-small ws-muted">{analysis.notes}</p>
                    <div className="ws-chip-row">
                      <span className="ws-chip">{analysis.plantPart.replace("_", " ")}</span>
                      <span className="ws-chip">{analysis.mediaType}</span>
                      <span className="ws-chip">Quality: good</span>
                    </div>
                    <div className="ws-queue-card-actions">
                      <button type="button" className="ws-button ws-button-primary" onClick={() => openReview(analysis)}>
                        <Icon name="check" size={15} /> Review case
                      </button>
                      <Link href={`/analysis?focus=${analysis.id}`} className="ws-button ws-button-secondary">Open evidence</Link>
                      <button type="button" className="ws-button ws-button-ghost" onClick={() => openReview(analysis)}>
                        <Icon name="edit" size={15} /> Correct match
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
            {pending.length === 0 ? <EmptyState title="Queue is clear" body="No farmer submissions are waiting for verification." icon="check" /> : null}
          </section>

          <aside className="ws-stack">
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Recent decisions</h2><Badge tone="neutral">{verified.length}</Badge></div>
              <ul className="ws-activity-list">
                {verified.slice(0, 4).map((analysis) => (
                  <li key={analysis.id}>
                    <span className="ws-activity-dot ws-tone-ok" />
                    <div>
                      <strong>{analysis.subjectLabel}</strong>
                      <span className="ws-small ws-muted">{analysis.reviewStatus} by {analysis.reviewer}</span>
                    </div>
                    <Link href={`/analysis?focus=${analysis.id}`} className="ws-link">Open</Link>
                  </li>
                ))}
              </ul>
            </section>
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Verification SLA</h2><Badge tone="warn">Monitor</Badge></div>
              <div className="ws-sla">
                <ProgressBar value={72} label="Within 24 hours" tone="ok" />
                <ProgressBar value={18} label="24–48 hours" tone="warn" />
                <ProgressBar value={10} label="Over 48 hours" tone="bad" />
              </div>
              <p className="ws-small ws-muted">High-severity and rapid-spread cases are prioritised regardless of age.</p>
            </section>
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Role permissions</h2></div>
              <ul className="ws-checklist">
                <li><Icon name="check" size={15} /> Verify AI diagnosis</li>
                <li><Icon name="check" size={15} /> Correct pest or disease label</li>
                <li><Icon name="check" size={15} /> Add recommendations</li>
                <li><Icon name="check" size={15} /> Upload inspection photos</li>
                <li><Icon name="check" size={15} /> Update inspection status</li>
              </ul>
            </section>
          </aside>
        </div>
      ) : null}

      {tab === "inspections" ? (
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div><p className="ws-eyebrow">Assigned visits</p><h2>Field inspections</h2></div>
            <Link href="/monitoring" className="ws-link">Open monitoring <Icon name="arrow" size={14} /></Link>
          </div>
          <div className="ws-table-wrap">
            <table className="ws-table">
              <thead>
                <tr><th>Inspection</th><th>Farm / target</th><th>Assigned</th><th>Scheduled</th><th>Status</th><th>Farmer report</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {state.inspections.map((inspection) => (
                  <tr key={inspection.id}>
                    <td><strong>{inspection.title}</strong><span className="ws-small ws-muted ws-block">{inspection.type.replace("_", " ")}</span></td>
                    <td>{inspection.farmName}<span className="ws-small ws-muted ws-block">{inspection.target}</span></td>
                    <td>{inspection.assignee}</td>
                    <td>{formatDate(inspection.scheduledFor)}</td>
                    <td>
                      <select
                        value={inspection.status}
                        aria-label={`Status for ${inspection.title}`}
                        onChange={(event) => updateInspection(inspection.id, { status: event.target.value as typeof inspection.status })}
                      >
                        <option value="scheduled">Scheduled</option>
                        <option value="in_progress">In progress</option>
                        <option value="completed">Completed</option>
                        <option value="overdue">Overdue</option>
                      </select>
                    </td>
                    <td className="ws-small ws-muted">{inspection.farmerReport ?? "—"}</td>
                    <td>
                      <button type="button" className="ws-link-button" onClick={() => setPhotoFor(inspection.id)}>
                        Upload photo
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {tab === "regional" ? (
        <div className="ws-two-col ws-two-col-wide">
          <section className="ws-panel">
            <div className="ws-panel-head">
              <div><p className="ws-eyebrow">Regional evidence</p><h2>Reported cases</h2></div>
              <Badge tone="neutral">{state.cases.length} records</Badge>
            </div>
            <div className="ws-table-wrap">
              <table className="ws-table">
                <thead><tr><th>Pest</th><th>Crop</th><th>Location</th><th>Reported</th><th>Severity</th><th>Cases</th><th>Status</th></tr></thead>
                <tbody>
                  {state.cases.map((item) => (
                    <tr key={item.id}>
                      <td><strong>{item.pest}</strong></td>
                      <td>{item.crop}</td>
                      <td>{item.village}, {item.district}</td>
                      <td>{formatDate(item.reportedAt)}</td>
                      <td><SeverityPill severity={item.severity} /></td>
                      <td>{item.cases}</td>
                      <td>{item.verified ? <Badge tone="ok">Verified</Badge> : <Badge tone="warn">Pending</Badge>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <aside className="ws-stack">
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Regional summary</h2></div>
              <dl className="ws-detail-list">
                <div><dt>Districts covered</dt><dd>{new Set(state.cases.map((item) => item.district)).size}</dd></div>
                <div><dt>Verified clusters</dt><dd>{verifiedCases.length}</dd></div>
                <div><dt>Total cases</dt><dd>{state.cases.reduce((sum, item) => sum + item.cases, 0)}</dd></div>
                <div><dt>High-risk outlooks</dt><dd>{state.riskRegions.filter((region) => region.band === "high" || region.band === "urgent").length}</dd></div>
              </dl>
              <Link href="/hotspots" className="ws-button ws-button-secondary ws-button-block">Open hotspot map</Link>
            </section>
            <section className="ws-panel">
              <div className="ws-panel-head"><h2>Coverage notes</h2></div>
              <ul className="ws-checklist">
                <li><Icon name="map" size={15} /> Krishnagiri: partial coverage</li>
                <li><Icon name="map" size={15} /> Dharmapuri: good coverage</li>
                <li><Icon name="map" size={15} /> Salem: good coverage</li>
                <li><Icon name="alert" size={15} /> Kelamangalam: only 1 report</li>
              </ul>
            </section>
          </aside>
        </div>
      ) : null}

      <Modal
        open={active !== null}
        onClose={() => setActive(null)}
        title={active ? `Review ${active.subjectLabel}` : "Review"}
        footer={
          <>
            <button type="button" className="ws-button ws-button-ghost" onClick={() => setActive(null)}>Cancel</button>
            <button type="submit" form="review-form" className="ws-button ws-button-primary">Save review</button>
          </>
        }
      >
        {active ? (
          <form id="review-form" onSubmit={submitReview} className="ws-form">
            <div className="ws-review-grid">
              <div>
                <PhotoTile tone={active.imageTone} mediaType={active.mediaType} label={active.subjectLabel} size="lg" />
                <p className="ws-small ws-muted">{active.farmName} · {formatDateTime(active.createdAt)}</p>
              </div>
              <div>
                <p className="ws-eyebrow">AI suggestion</p>
                <h3>{active.pest ?? active.disease ?? "No specific match"}</h3>
                <div className="ws-chip-row">
                  <SeverityPill severity={active.severity} />
                  <span className="ws-chip">{active.confidenceBand} confidence</span>
                  <span className="ws-chip">Not calibrated</span>
                </div>
                <p className="ws-small ws-muted">{active.notes}</p>
                <HealthPill health="watch" />
              </div>
            </div>
            <Field label="Decision">
              <div className="ws-verdict-row">
                {(["verified", "corrected", "rejected"] as const).map((option) => (
                  <button
                    key={option}
                    type="button"
                    className={verdict === option ? "ws-verdict ws-verdict-active" : "ws-verdict"}
                    onClick={() => setVerdict(option)}
                  >
                    {option === "verified" ? "Verify AI match" : option === "corrected" ? "Correct diagnosis" : "Reject / unclear"}
                  </button>
                ))}
              </div>
            </Field>
            {verdict === "corrected" ? (
              <Field label="Corrected pest or disease"><input value={correctedLabel} onChange={(event) => setCorrectedLabel(event.target.value)} placeholder="e.g. Early blight" required /></Field>
            ) : null}
            <Field label="Reviewer note"><textarea rows={3} value={note} onChange={(event) => setNote(event.target.value)} placeholder="What evidence supports this decision?" /></Field>
            <Field label="Recommendations" hint="One recommendation per line. No product names, doses or intervals.">
              <textarea rows={3} value={recommendations} onChange={(event) => setRecommendations(event.target.value)} placeholder={"Scout the block every 3 days\nRequest a field visit if spread continues"} />
            </Field>
            <p className="ws-small ws-muted">The stored AI prediction is preserved; this review is appended to the audit trail.</p>
          </form>
        ) : null}
      </Modal>

      <Modal open={photoFor !== null} onClose={() => setPhotoFor(null)} title="Upload inspection photograph">
        <div className="ws-form">
          <p className="ws-small ws-muted">Add a field photograph to the inspection record. GPS and timestamp are attached with permission.</p>
          <label className="ws-dropzone">
            <Icon name="camera" size={26} />
            <strong>Choose or capture a photo</strong>
            <span className="ws-small ws-muted">JPEG or PNG · compressed before upload</span>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              className="ws-hidden-input"
              onChange={() => {
                if (photoFor) {
                  updateInspection(photoFor, { afterTone: 3, status: "completed", notes: "Inspection photograph uploaded from the field." });
                }
                setPhotoFor(null);
              }}
            />
          </label>
          <div className="ws-chip-row">
            <Badge tone="info">GPS permission requested</Badge>
            <Badge tone="neutral">Immutable original retained</Badge>
          </div>
        </div>
      </Modal>
    </div>
  );
}

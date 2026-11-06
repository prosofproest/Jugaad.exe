"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import {
  Badge,
  EmptyState,
  Field,
  Icon,
  Modal,
  PageHeader,
  PhotoTile,
  ProgressBar,
  StatCard,
  Tabs,
} from "@/components/workspace/ui";
import { formatDate, formatDateTime, isoDateInput } from "@/lib/format";
import { useWorkspace } from "@/lib/workspace/store";
import type { Inspection } from "@/lib/workspace/types";

type Filter = "upcoming" | "completed" | "follow_up" | "failed";

const TYPE_LABEL: Record<Inspection["type"], string> = {
  inspection: "Farm inspection",
  scouting: "Pest scouting",
  follow_up: "Follow-up observation",
  treatment_check: "Treatment check",
};

function statusBadge(status: Inspection["status"]) {
  if (status === "completed") return <Badge tone="ok">Completed</Badge>;
  if (status === "in_progress") return <Badge tone="info">In progress</Badge>;
  if (status === "overdue") return <Badge tone="bad">Overdue</Badge>;
  return <Badge tone="warn">Scheduled</Badge>;
}

export default function MonitoringPage() {
  const { state, scheduleInspection, updateInspection } = useWorkspace();
  const [filter, setFilter] = useState<Filter>("upcoming");
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [outcomeFor, setOutcomeFor] = useState<Inspection | null>(null);
  const [compare, setCompare] = useState<Inspection | null>(null);
  const [form, setForm] = useState({
    farmId: state.farms[0]?.id ?? "",
    title: "",
    type: "scouting" as Inspection["type"],
    crop: "Tomato",
    target: "",
    scheduledFor: isoDateInput(new Date()),
    assignee: "Ravi Kumar",
    notes: "",
  });
  const [outcome, setOutcome] = useState({
    status: "completed" as Inspection["status"],
    treatment: "",
    effectiveness: "60",
    recovery: "50",
    failed: false,
    notes: "",
  });

  const filtered = useMemo(() => {
    return state.inspections.filter((inspection) => {
      if (filter === "upcoming") return inspection.status === "scheduled" || inspection.status === "in_progress" || inspection.status === "overdue";
      if (filter === "completed") return inspection.status === "completed";
      if (filter === "follow_up") return inspection.type === "follow_up" || inspection.type === "treatment_check";
      return inspection.failedTreatment;
    });
  }, [state.inspections, filter]);

  const upcoming = state.inspections
    .filter((inspection) => inspection.status === "scheduled" || inspection.status === "overdue")
    .sort((a, b) => a.scheduledFor.localeCompare(b.scheduledFor));
  const completed = state.inspections.filter((inspection) => inspection.status === "completed");
  const failed = state.inspections.filter((inspection) => inspection.failedTreatment);
  const avgRecovery = completed.length
    ? Math.round(completed.reduce((sum, item) => sum + (item.recovery ?? 0), 0) / completed.length)
    : 0;

  function submitSchedule(event: React.FormEvent) {
    event.preventDefault();
    if (!form.title.trim()) return;
    scheduleInspection({
      farmId: form.farmId,
      title: form.title.trim(),
      type: form.type,
      crop: form.crop,
      target: form.target || "Whole farm",
      scheduledFor: new Date(form.scheduledFor).toISOString(),
      assignee: form.assignee,
      notes: form.notes,
    });
    setScheduleOpen(false);
    setForm((current) => ({ ...current, title: "", target: "", notes: "" }));
  }

  function openOutcome(inspection: Inspection) {
    setOutcome({
      status: inspection.status === "completed" ? "completed" : "completed",
      treatment: inspection.treatment ?? "",
      effectiveness: String(inspection.effectiveness ?? 60),
      recovery: String(inspection.recovery ?? 50),
      failed: inspection.failedTreatment,
      notes: inspection.notes,
    });
    setOutcomeFor(inspection);
  }

  function saveOutcome(event: React.FormEvent) {
    event.preventDefault();
    if (!outcomeFor) return;
    updateInspection(outcomeFor.id, {
      status: outcome.status,
      treatment: outcome.treatment || null,
      effectiveness: Number(outcome.effectiveness) || 0,
      recovery: Number(outcome.recovery) || 0,
      failedTreatment: outcome.failed,
      notes: outcome.notes,
      afterTone: 3,
    });
    setOutcomeFor(null);
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Monitoring & recovery"
        title="Schedule scouting, compare evidence and track recovery"
        lede="Inspection reminders, follow-up observations, before/after comparison, treatment effectiveness and failed-treatment flags in one place."
        actions={
          <button type="button" className="ws-button ws-button-primary" onClick={() => setScheduleOpen(true)}>
            <Icon name="calendar" size={17} /> Schedule inspection
          </button>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Upcoming" value={upcoming.length} detail={upcoming[0] ? `Next ${formatDate(upcoming[0].scheduledFor)}` : "Nothing scheduled"} icon="calendar" tone="warn" />
        <StatCard label="Completed" value={completed.length} detail="With field notes" icon="check" tone="ok" />
        <StatCard label="Average recovery" value={`${avgRecovery}%`} detail="Across completed follow-ups" icon="leaf" tone="brand" />
        <StatCard label="Failed treatments" value={failed.length} detail="Needs a new field decision" icon="alert" tone={failed.length > 0 ? "bad" : "ok"} />
      </div>

      <div className="ws-two-col ws-two-col-wide">
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div><p className="ws-eyebrow">Reminders</p><h2>Next inspections</h2></div>
            <Link href="/notifications" className="ws-link">Reminders <Icon name="arrow" size={14} /></Link>
          </div>
          <ul className="ws-reminder-list">
            {upcoming.slice(0, 4).map((inspection) => (
              <li key={inspection.id}>
                <div className="ws-reminder-date">
                  <strong>{new Date(inspection.scheduledFor).getDate()}</strong>
                  <span>{new Date(inspection.scheduledFor).toLocaleDateString("en-IN", { month: "short" })}</span>
                </div>
                <div className="ws-reminder-body">
                  <div className="ws-reminder-top">
                    <Badge tone={inspection.status === "overdue" ? "bad" : "neutral"}>{TYPE_LABEL[inspection.type]}</Badge>
                    {statusBadge(inspection.status)}
                  </div>
                  <strong>{inspection.title}</strong>
                  <span className="ws-small ws-muted">{inspection.farmName} · {inspection.target} · {inspection.assignee}</span>
                </div>
                <button type="button" className="ws-button ws-button-secondary" onClick={() => openOutcome(inspection)}>
                  Record outcome
                </button>
              </li>
            ))}
          </ul>
          {upcoming.length === 0 ? <EmptyState title="No inspections scheduled" body="Schedule scouting so early damage is not missed." action={<button type="button" className="ws-button ws-button-primary" onClick={() => setScheduleOpen(true)}>Schedule now</button>} /> : null}
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">Recovery summary</p><h2>Treatment effectiveness</h2></div></div>
          <div className="ws-recovery-summary">
            {completed.slice(0, 4).map((inspection) => (
              <div key={inspection.id}>
                <div className="ws-recovery-summary-head">
                  <div><strong>{inspection.title}</strong><span className="ws-small ws-muted">{inspection.crop} · {inspection.target}</span></div>
                  {inspection.failedTreatment ? <Badge tone="bad">Failed</Badge> : <Badge tone="ok">On track</Badge>}
                </div>
                <ProgressBar value={inspection.recovery ?? 0} label="Recovery" tone={(inspection.recovery ?? 0) >= 60 ? "ok" : "warn"} />
                <ProgressBar value={inspection.effectiveness ?? 0} label="Effectiveness" tone="brand" />
                <div className="ws-chip-row">
                  <span className="ws-chip">{inspection.treatment ?? "Monitor only"}</span>
                  {inspection.recovery !== null ? <span className="ws-chip">Reduction {inspection.recovery}%</span> : null}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <Tabs
        label="Inspection filters"
        value={filter}
        onChange={setFilter}
        tabs={[
          { value: "upcoming", label: "Upcoming", count: upcoming.length },
          { value: "completed", label: "Completed", count: completed.length },
          { value: "follow_up", label: "Follow-ups", count: state.inspections.filter((item) => item.type === "follow_up" || item.type === "treatment_check").length },
          { value: "failed", label: "Failed treatments", count: failed.length },
        ]}
      />

      <div className="ws-inspection-grid">
        {filtered.map((inspection) => (
          <article key={inspection.id} className="ws-inspection-card">
            <div className="ws-inspection-head">
              <div>
                <p className="ws-eyebrow">{TYPE_LABEL[inspection.type]}</p>
                <h3>{inspection.title}</h3>
                <span className="ws-small ws-muted">{inspection.farmName} · {formatDateTime(inspection.scheduledFor)}</span>
              </div>
              {statusBadge(inspection.status)}
            </div>
            <div className="ws-inspection-meta">
              <span><Icon name="leaf" size={14} /> {inspection.crop}</span>
              <span><Icon name="location" size={14} /> {inspection.target}</span>
              <span><Icon name="user" size={14} /> {inspection.assignee}</span>
            </div>
            <p className="ws-small">{inspection.notes}</p>
            {inspection.farmerReport ? (
              <div className="ws-farmer-report">
                <strong>Farmer report</strong>
                <p className="ws-small">{inspection.farmerReport}</p>
              </div>
            ) : null}
            {inspection.beforeTone !== null ? (
              <div className="ws-inspection-photos">
                <div>
                  <PhotoTile tone={inspection.beforeTone} label="Before treatment" size="sm" />
                  <span className="ws-small">Before</span>
                </div>
                <Icon name="arrow" size={16} />
                <div>
                  <PhotoTile tone={inspection.afterTone ?? inspection.beforeTone} label="After treatment" size="sm" />
                  <span className="ws-small">After</span>
                </div>
                <button type="button" className="ws-link-button" onClick={() => setCompare(inspection)}>Compare</button>
              </div>
            ) : null}
            {inspection.effectiveness !== null ? (
              <div className="ws-inspection-bars">
                <ProgressBar value={inspection.recovery ?? 0} label="Recovery" tone="ok" />
                <ProgressBar value={inspection.effectiveness ?? 0} label="Effectiveness" tone="brand" />
              </div>
            ) : null}
            {inspection.failedTreatment ? (
              <div className="ws-banner ws-banner-warn ws-banner-compact">
                <Icon name="alert" size={16} />
                <p>This treatment did not meet its goal. Record a failed outcome and ask for a new field decision.</p>
              </div>
            ) : null}
            <div className="ws-inspection-actions">
              <button type="button" className="ws-button ws-button-secondary" onClick={() => openOutcome(inspection)}>
                <Icon name="edit" size={15} /> Record outcome
              </button>
              {inspection.beforeTone !== null ? (
                <button type="button" className="ws-button ws-button-ghost" onClick={() => setCompare(inspection)}>
                  View comparison
                </button>
              ) : null}
              <Link href="/scan" className="ws-button ws-button-ghost"><Icon name="camera" size={15} /> Add observation</Link>
            </div>
          </article>
        ))}
      </div>
      {filtered.length === 0 ? <EmptyState title="Nothing in this list" body="Schedule a new inspection or choose another filter." icon="monitoring" /> : null}

      <Modal
        open={scheduleOpen}
        onClose={() => setScheduleOpen(false)}
        title="Schedule an inspection"
        footer={
          <>
            <button type="button" className="ws-button ws-button-ghost" onClick={() => setScheduleOpen(false)}>Cancel</button>
            <button type="submit" form="inspection-form" className="ws-button ws-button-primary">Schedule</button>
          </>
        }
      >
        <form id="inspection-form" onSubmit={submitSchedule} className="ws-form">
          <Field label="Title"><input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Weekly pinworm scouting" required /></Field>
          <div className="ws-form-grid">
            <Field label="Farm">
              <select value={form.farmId} onChange={(event) => setForm({ ...form, farmId: event.target.value })}>
                {state.farms.map((farm) => <option key={farm.id} value={farm.id}>{farm.name}</option>)}
              </select>
            </Field>
            <Field label="Type">
              <select value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value as Inspection["type"] })}>
                <option value="inspection">Farm inspection</option>
                <option value="scouting">Pest scouting</option>
                <option value="follow_up">Follow-up observation</option>
                <option value="treatment_check">Treatment check</option>
              </select>
            </Field>
          </div>
          <div className="ws-form-grid">
            <Field label="Crop">
              <select value={form.crop} onChange={(event) => setForm({ ...form, crop: event.target.value })}>
                <option>Tomato</option><option>Chilli</option><option>Brinjal</option><option>Mango</option><option>Maize</option><option>Cowpea</option>
              </select>
            </Field>
            <Field label="Target plot or plant"><input value={form.target} onChange={(event) => setForm({ ...form, target: event.target.value })} placeholder="North Plot · Section A1" /></Field>
          </div>
          <div className="ws-form-grid">
            <Field label="Date and time">
              <input type="datetime-local" value={form.scheduledFor} onChange={(event) => setForm({ ...form, scheduledFor: event.target.value })} />
            </Field>
            <Field label="Assignee">
              <select value={form.assignee} onChange={(event) => setForm({ ...form, assignee: event.target.value })}>
                <option>Ravi Kumar</option><option>Arun Prasad</option><option>Dr. Meera Sundaram</option>
              </select>
            </Field>
          </div>
          <Field label="Instructions"><textarea rows={3} value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="What should be checked?" /></Field>
        </form>
      </Modal>

      <Modal
        open={outcomeFor !== null}
        onClose={() => setOutcomeFor(null)}
        title="Record inspection outcome"
        footer={
          <>
            <button type="button" className="ws-button ws-button-ghost" onClick={() => setOutcomeFor(null)}>Cancel</button>
            <button type="submit" form="outcome-form" className="ws-button ws-button-primary">Save outcome</button>
          </>
        }
      >
        <form id="outcome-form" onSubmit={saveOutcome} className="ws-form">
          <p className="ws-small ws-muted">{outcomeFor?.title} · {outcomeFor?.target}</p>
          <Field label="Status">
            <select value={outcome.status} onChange={(event) => setOutcome({ ...outcome, status: event.target.value as Inspection["status"] })}>
              <option value="completed">Completed</option>
              <option value="in_progress">In progress</option>
              <option value="scheduled">Still scheduled</option>
              <option value="overdue">Overdue</option>
            </select>
          </Field>
          <Field label="Treatment or action taken"><input value={outcome.treatment} onChange={(event) => setOutcome({ ...outcome, treatment: event.target.value })} placeholder="Pruning and sanitation (no spray advice)" /></Field>
          <div className="ws-form-grid">
            <Field label="Recovery (%)"><input type="number" min="0" max="100" value={outcome.recovery} onChange={(event) => setOutcome({ ...outcome, recovery: event.target.value })} /></Field>
            <Field label="Effectiveness (%)"><input type="number" min="0" max="100" value={outcome.effectiveness} onChange={(event) => setOutcome({ ...outcome, effectiveness: event.target.value })} /></Field>
          </div>
          <label className="ws-check">
            <input type="checkbox" checked={outcome.failed} onChange={(event) => setOutcome({ ...outcome, failed: event.target.checked })} />
            Mark treatment as failed / needs a new decision
          </label>
          <Field label="Field notes"><textarea rows={3} value={outcome.notes} onChange={(event) => setOutcome({ ...outcome, notes: event.target.value })} /></Field>
          <p className="ws-small ws-muted">Add an after photo from Scan &amp; capture. Recovery is a field judgement and is shown with its date.</p>
        </form>
      </Modal>

      <Modal open={compare !== null} onClose={() => setCompare(null)} title="Compare before and after">
        {compare ? (
          <div className="ws-compare-modal">
            <div className="ws-compare-col">
              <p className="ws-eyebrow">Before</p>
              <PhotoTile tone={compare.beforeTone ?? 5} label="Before treatment" size="lg" />
              <p className="ws-small ws-muted">Initial observation · {formatDate(compare.scheduledFor)}</p>
            </div>
            <div className="ws-compare-col">
              <p className="ws-eyebrow">After</p>
              <PhotoTile tone={compare.afterTone ?? compare.beforeTone ?? 5} label="After treatment" size="lg" />
              <p className="ws-small ws-muted">Follow-up · {compare.treatment ?? "No treatment recorded"}</p>
            </div>
            <div className="ws-compare-summary">
              <ProgressBar value={compare.recovery ?? 0} label="Recovery" tone="ok" />
              <ProgressBar value={compare.effectiveness ?? 0} label="Treatment effectiveness" tone="brand" />
              <p className="ws-small ws-muted">{compare.notes}</p>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}

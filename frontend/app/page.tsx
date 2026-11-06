"use client";

import Link from "next/link";

import { AnalysisReport } from "@/components/workspace/analysis-report";
import { FarmMap } from "@/components/workspace/farm-map";
import {
  Badge,
  HealthPill,
  Icon,
  PageHeader,
  ProgressBar,
  SeverityPill,
  Sparkline,
  StatCard,
  EmptyState,
} from "@/components/workspace/ui";
import { formatDate, formatDateTime, relativeTime } from "@/lib/format";
import { cropGroupHealth, useWorkspace } from "@/lib/workspace/store";
import type { Role } from "@/lib/workspace/types";

const ROLE_COPY: Record<Role, { label: string; title: string; lede: string }> = {
  farmer: {
    label: "Farmer workspace",
    title: "Your farm at a glance",
    lede: "Scout early, compare observations and keep one clear next step in front of you.",
  },
  expert: {
    label: "Expert workspace",
    title: "Verification and field inspection",
    lede: "Triage uncertain observations, correct automated matches and record approved recommendations.",
  },
  agent: {
    label: "Field agent workspace",
    title: "Your assigned visits and scouting",
    lede: "See farmer reports, scheduled inspections and the nearest verification requests.",
  },
  admin: {
    label: "Administrator workspace",
    title: "Coverage, backlog and regional signals",
    lede: "Track verified cases, outstanding reviews and data coverage without merging risk and status.",
  },
};

export default function DashboardPage() {
  const { state, role } = useWorkspace();
  const farm = state.farms[0];
  const copy = ROLE_COPY[role];

  const plants = state.plants.filter((plant) => plant.farmId === farm?.id);
  const healthyCount = plants.filter((plant) => plant.health === "healthy").length;
  const healthScore = plants.length > 0 ? Math.round((healthyCount / plants.length) * 100) : 0;
  const pending = state.analyses.filter((analysis) => analysis.reviewStatus === "pending");
  const activeInspections = state.inspections.filter(
    (inspection) => inspection.status === "scheduled" || inspection.status === "in_progress",
  );
  const dueToday = state.inspections.filter(
    (inspection) =>
      inspection.status === "scheduled" &&
      new Date(inspection.scheduledFor).toDateString() === new Date().toDateString(),
  );
  const critical = state.analyses.filter(
    (analysis) => analysis.severity === "critical" || analysis.severity === "high",
  );
  const verifiedCases = state.cases.filter((item) => item.verified).length;
  const queued = state.captures.filter((item) => item.syncState !== "synced").length;
  const unread = state.notifications.filter((item) => !item.read).length;

  const farmGroups = state.cropGroups.filter((group) => group.farmId === farm?.id);
  const latestAnalysis = state.analyses[0];

  const priorities = (() => {
    if (role === "expert") {
      return pending.slice(0, 3).map((analysis) => ({
        href: "/expert",
        title: `Review ${analysis.subjectLabel}`,
        detail: `Possible ${analysis.pest ?? analysis.disease} · ${analysis.severity} severity`,
        tone: analysis.severity === "critical" || analysis.severity === "high" ? "bad" : "warn",
        tag: "Verification",
      }));
    }
    if (role === "agent") {
      return state.inspections
        .filter((inspection) => inspection.assignee === "Arun Prasad")
        .slice(0, 3)
        .map((inspection) => ({
          href: "/monitoring",
          title: inspection.title,
          detail: `${inspection.farmName} · ${formatDate(inspection.scheduledFor)} · ${inspection.status.replace("_", " ")}`,
          tone: inspection.status === "overdue" ? "bad" : "warn",
          tag: "Field visit",
        }));
    }
    if (role === "admin") {
      return [
        {
          href: "/hotspots",
          title: "Late blight urgent in Dharmapuri",
          detail: "6 verified cases · coverage good · valid 6–8 Nov",
          tone: "bad",
          tag: "Regional risk",
        },
        {
          href: "/expert",
          title: `${pending.length} observations awaiting verification`,
          detail: "Oldest request is 18 hours old",
          tone: "warn",
          tag: "Backlog",
        },
        {
          href: "/map",
          title: "Coverage gap in Kelamangalam",
          detail: "Only 1 report in the last 14 days",
          tone: "neutral",
          tag: "Coverage",
        },
      ];
    }
    return [
      ...critical.slice(0, 2).map((analysis) => ({
        href: `/analysis?focus=${analysis.id}`,
        title: analysis.subjectLabel,
        detail: `Possible ${analysis.pest ?? analysis.disease} · ${analysis.severity} severity`,
        tone: analysis.severity === "critical" ? "bad" : "warn",
        tag: "High priority",
      })),
      ...(queued > 0
        ? [
            {
              href: "/scan",
              title: `${queued} capture${queued === 1 ? "" : "s"} waiting to sync`,
              detail: "Saved on this device while offline",
              tone: "warn",
              tag: "Offline queue",
            },
          ]
        : []),
    ];
  })();

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow={copy.label}
        title={`${greeting()}, ${state.currentUser.name.split(" ")[0]}`}
        lede={copy.lede}
        actions={
          <>
            <Link href="/scan" className="ws-button ws-button-primary">
              <Icon name="camera" size={17} /> Scan a plant
            </Link>
            <Link href="/farms" className="ws-button ws-button-secondary">
              <Icon name="plus" size={16} /> Add farm
            </Link>
          </>
        }
      />

      <div className="ws-hero">
        <div className="ws-hero-main">
          <div className="ws-hero-copy">
            <span className="ws-hero-pill">
              <span className="ws-live-dot" /> {farm?.name}
            </span>
            <h2>{healthScore >= 70 ? "The farm is mostly stable, with two blocks to watch." : "Several blocks need a field check this week."}</h2>
            <p>
              {critical.length} high-severity observation{critical.length === 1 ? "" : "s"} and{" "}
              {pending.length} pending expert review{pending.length === 1 ? "" : "s"} across{" "}
              {state.farms.length} farms. {queued > 0 ? `${queued} captures are saved offline.` : "All captures are synced."}
            </p>
            <div className="ws-hero-actions">
              <Link href="/map" className="ws-button ws-button-primary">
                Open farm health map <Icon name="arrow" size={16} />
              </Link>
              <Link href="/expert" className="ws-button ws-button-ghost">
                Review queue ({pending.length})
              </Link>
            </div>
          </div>
          <div className="ws-health-ring" aria-label={`Farm health score ${healthScore} percent`}>
            <svg viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="50" className="ws-ring-track" />
              <circle
                cx="60"
                cy="60"
                r="50"
                className="ws-ring-value"
                strokeDasharray={`${(healthScore / 100) * 314} 314`}
              />
            </svg>
            <div>
              <strong>{healthScore}%</strong>
              <span>plants healthy</span>
            </div>
          </div>
        </div>
        <div className="ws-hero-footer">
          <span><Icon name="plant" size={15} /> {plants.length} plants tracked</span>
          <span><Icon name="farm" size={15} /> {state.plots.filter((plot) => plot.farmId === farm?.id).length} plots</span>
          <span><Icon name="bell" size={15} /> {unread} unread alert{unread === 1 ? "" : "s"}</span>
          <span><Icon name="sync" size={15} /> {queued === 0 ? "Everything synced" : `${queued} queued`}</span>
        </div>
      </div>

      <div className="ws-stat-grid">
        <StatCard
          label={role === "admin" ? "Verified cases (14 d)" : "Crop groups"}
          value={role === "admin" ? verifiedCases : farmGroups.length}
          detail={role === "admin" ? "Across 3 districts" : `${farm?.areaAcres ?? 0} acres total`}
          icon={role === "admin" ? "shield" : "leaf"}
          tone="brand"
        />
        <StatCard
          label="High severity"
          value={critical.length}
          detail="Needs field follow-up"
          icon="alert"
          tone="bad"
        />
        <StatCard
          label="Pending reviews"
          value={pending.length}
          detail="Oldest 18 hours"
          icon="expert"
          tone="warn"
        />
        <StatCard
          label="Next inspection"
          value={dueToday.length > 0 ? "Today" : activeInspections[0] ? formatDate(activeInspections[0].scheduledFor) : "None"}
          detail={activeInspections[0]?.title ?? "Schedule a scouting walk"}
          icon="calendar"
          tone="default"
        />
      </div>

      <div className="ws-two-col ws-two-col-wide">
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">{role === "admin" ? "Regional signals" : "Priority queue"}</p>
              <h2>{role === "farmer" ? "Start here" : "Needs your attention"}</h2>
            </div>
            <Link href="/notifications" className="ws-link">
              All alerts <Icon name="arrow" size={14} />
            </Link>
          </div>
          {priorities.length > 0 ? (
            <ul className="ws-priority-list">
              {priorities.map((item) => (
                <li key={item.title}>
                  <Link href={item.href} className="ws-priority">
                    <span className={`ws-priority-bar ws-tone-${item.tone}`} />
                    <span className="ws-priority-body">
                      <span className="ws-priority-top">
                        <Badge tone={item.tone === "bad" ? "bad" : item.tone === "warn" ? "warn" : "neutral"}>
                          {item.tag}
                        </Badge>
                        <span className="ws-small ws-muted">{item.tone === "bad" ? "Action needed" : "This week"}</span>
                      </span>
                      <strong>{item.title}</strong>
                      <span className="ws-small ws-muted">{item.detail}</span>
                    </span>
                    <Icon name="arrow" size={17} />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              title="Nothing urgent right now"
              body="Keep scouting on schedule. New observations will appear here with one clear next step."
              icon="check"
            />
          )}
        </section>

        <section className="ws-panel ws-panel-map">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Farm health map</p>
              <h2>{farm?.name}</h2>
            </div>
            <Link href="/map" className="ws-link">
              Full map <Icon name="arrow" size={14} />
            </Link>
          </div>
          {farm ? <FarmMap farm={farm} compact showPlants /> : null}
        </section>
      </div>

      <div className="ws-two-col">
        <section className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Crop-wise health</p>
              <h2>Blocks in this farm</h2>
            </div>
            <Badge tone="neutral">{farmGroups.length} blocks</Badge>
          </div>
          <ul className="ws-crop-list">
            {farmGroups.slice(0, 5).map((group) => {
              const health = cropGroupHealth(state, group.id);
              const groupPlants = state.plants.filter((plant) => plant.cropGroupId === group.id);
              const healthy = groupPlants.filter((plant) => plant.health === "healthy").length;
              return (
                <li key={group.id}>
                  <div className="ws-crop-icon">
                    <Icon name="leaf" size={18} />
                  </div>
                  <div className="ws-crop-info">
                    <div className="ws-crop-top">
                      <strong>{group.name}</strong>
                      <HealthPill health={health} />
                    </div>
                    <span className="ws-small ws-muted">
                      {group.crop} · {group.variety} · {group.stage}
                    </span>
                    <ProgressBar
                      value={groupPlants.length > 0 ? Math.round((healthy / groupPlants.length) * 100) : 100}
                      label={`${healthy}/${groupPlants.length} plants healthy`}
                      tone={health === "healthy" ? "ok" : health === "watch" ? "warn" : "bad"}
                    />
                  </div>
                  <Link href={`/farms/${group.farmId}`} className="ws-icon-button" aria-label={`Open ${group.name}`}>
                    <Icon name="arrow" size={16} />
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Latest assessment</p>
              <h2>Recent photo triage</h2>
            </div>
            <Link href="/analysis" className="ws-link">
              All analyses <Icon name="arrow" size={14} />
            </Link>
          </div>
          {latestAnalysis ? (
            <div className="ws-latest-assessment">
              <div className="ws-latest-top">
                <div>
                  <strong>{latestAnalysis.pest ?? latestAnalysis.disease ?? "No specific match"}</strong>
                  <span className="ws-small ws-muted">
                    {latestAnalysis.subjectLabel} · {relativeTime(latestAnalysis.createdAt)}
                  </span>
                </div>
                <SeverityPill severity={latestAnalysis.severity} />
              </div>
              <p className="ws-small">{latestAnalysis.symptoms[0]}</p>
              <div className="ws-chip-row">
                <Badge tone="purple">{latestAnalysis.reviewStatus.replace("_", " ")}</Badge>
                <span className="ws-chip">Confidence: {latestAnalysis.confidenceBand}</span>
                <span className="ws-chip">Not calibrated</span>
              </div>
              <Link href={`/analysis?focus=${latestAnalysis.id}`} className="ws-button ws-button-secondary ws-button-block">
                Open assessment <Icon name="arrow" size={15} />
              </Link>
            </div>
          ) : null}
          <div className="ws-mini-trend">
            <div>
              <p className="ws-eyebrow">Detections, last 7 days</p>
              <strong>{state.analyses.length} assessments</strong>
            </div>
            <Sparkline values={[2, 3, 5, 4, 7, 6, 8]} label="Assessments per day" />
          </div>
        </section>
      </div>

      {latestAnalysis && role !== "admin" ? (
        <section>
          <div className="ws-section-head">
            <div>
              <p className="ws-eyebrow">Explainable result</p>
              <h2>Most recent AI analysis</h2>
            </div>
            <Link href="/analysis" className="ws-link">Open full analysis <Icon name="arrow" size={14} /></Link>
          </div>
          <AnalysisReport analysis={latestAnalysis} compact />
        </section>
      ) : null}
    </div>
  );
}

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

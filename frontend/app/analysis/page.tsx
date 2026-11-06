"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  Badge,
  EmptyState,
  Icon,
  PageHeader,
  StatCard,
  Tabs,
} from "@/components/workspace/ui";
import { formatDateTime } from "@/lib/format";
import {
  ApiError,
  listObservations,
  getObservationAssessment,
  requestObservationReview,
  type Assessment,
  type ObservationRecord,
} from "@/lib/api";
import { readSession } from "@/lib/auth";

type Filter = "all" | "pending" | "verified";

export default function AnalysisPage() {
  const [observations, setObservations] = useState<ObservationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [activeAssessment, setActiveAssessment] = useState<Assessment | null>(null);
  const [loadedAssessmentObsId, setLoadedAssessmentObsId] = useState<string | null>(null);
  const [reviewedId, setReviewedId] = useState<string | null>(null);

  const active = useMemo(
    () => observations.find((obs) => obs.id === activeId) ?? observations[0] ?? null,
    [observations, activeId],
  );

  const assessmentLoading = Boolean(active?.id && loadedAssessmentObsId !== active.id);

  useEffect(() => {
    let ignore = false;
    listObservations()
      .then((response) => {
        if (!ignore) {
          setObservations(response.items || []);
          if (response.items && response.items.length > 0) {
            setActiveId(response.items[0]?.id ?? null);
          }
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          if (err instanceof ApiError && err.status === 401) {
            setError("unauthorized");
          } else {
            setError(err instanceof Error ? err.message : "Failed to load observations");
          }
          setLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (!active?.id) return;
    const targetObsId = active.id;
    let ignore = false;
    getObservationAssessment(targetObsId)
      .then((assessment) => {
        if (!ignore) {
          setActiveAssessment(assessment);
          setLoadedAssessmentObsId(targetObsId);
        }
      })
      .catch(() => {
        if (!ignore) {
          setActiveAssessment(null);
          setLoadedAssessmentObsId(targetObsId);
        }
      });
    return () => {
      ignore = true;
    };
  }, [active?.id]);

  const filtered = useMemo(() => {
    return observations.filter((obs) => {
      if (filter === "pending") return obs.verification.status === "unverified" || obs.verification.status === "needs_visit";
      if (filter === "verified") return obs.verification.status === "confirmed" || obs.verification.status === "probable";
      return true;
    });
  }, [observations, filter]);

  const handleRequestReview = async () => {
    if (!active) return;
    try {
      await requestObservationReview(active.id, "Requested review from Analysis view");
      setReviewedId(active.id);
      const updated = await listObservations();
      setObservations(updated.items || []);
    } catch {
      // Failed to request review
    }
  };

  const isAuth = !!readSession();

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="AI analysis & observations"
        title="Verified Observations & Model Assessments"
        lede="Inspect actual observations recorded by farmers and extension workers with calibrated quality gates, confidence bands, and human verification trails."
        actions={
          <Link href="/scan" className="ws-button ws-button-primary">
            <Icon name="camera" size={17} /> New capture
          </Link>
        }
      />

      <div className="ws-stat-grid">
        <StatCard
          label="Total observations"
          value={observations.length}
          detail="Relational database records"
          icon="analysis"
          tone="brand"
        />
        <StatCard
          label="Pending review"
          value={observations.filter((o) => o.verification.status === "unverified" || o.verification.status === "needs_visit").length}
          detail="Awaiting human expert"
          icon="expert"
          tone="warn"
        />
        <StatCard
          label="Confirmed cases"
          value={observations.filter((o) => o.verification.status === "confirmed").length}
          detail="Pathologist verified"
          icon="shield"
          tone="ok"
        />
      </div>

      {!isAuth && (
        <div className="ws-banner ws-banner-info">
          <Icon name="user" size={18} />
          <div>
            <strong>Viewing public observation list</strong>
            <p>
              Sign in with a staff or farmer account to submit new observations or access private report details.
            </p>
          </div>
          <div className="ws-banner-actions">
            <Link href="/login" className="ws-button ws-button-secondary">
              Sign in
            </Link>
          </div>
        </div>
      )}

      {error && error !== "unauthorized" && (
        <div className="ws-banner ws-banner-bad">
          <Icon name="alert" size={18} />
          <div>
            <strong>Error connecting to backend</strong>
            <p>{error}. Ensure the FastAPI server is running on port 8000.</p>
          </div>
          <div className="ws-banner-actions">
            <button
              type="button"
              className="ws-button ws-button-secondary"
              onClick={() => {
                setLoading(true);
                listObservations()
                  .then((res) => {
                    setObservations(res.items || []);
                    setLoading(false);
                  })
                  .catch(() => setLoading(false));
              }}
            >
              Retry
            </button>
          </div>
        </div>
      )}

      <Tabs
        label="Observation filters"
        value={filter}
        onChange={(val) => setFilter(val as Filter)}
        tabs={[
          { value: "all", label: "All records", count: observations.length },
          {
            value: "pending",
            label: "Pending verification",
            count: observations.filter((o) => o.verification.status === "unverified" || o.verification.status === "needs_visit").length,
          },
          {
            value: "verified",
            label: "Verified",
            count: observations.filter((o) => o.verification.status === "confirmed" || o.verification.status === "probable").length,
          },
        ]}
      />

      {loading ? (
        <div className="ws-panel">
          <p className="ws-muted">Loading observations from backend API...</p>
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No observations found"
          body="There are currently no observations matching this filter in the PostgreSQL database. Capture an image or start a photo assessment to create one."
          action={
            <Link href="/scan" className="ws-button ws-button-primary">
              Scan or upload
            </Link>
          }
        />
      ) : (
        <div className="ws-two-col">
          <div className="ws-analysis-list">
            {filtered.map((obs) => {
              const selected = obs.id === active?.id;
              return (
                <button
                  key={obs.id}
                  type="button"
                  className={selected ? "ws-analysis-card ws-analysis-card-active" : "ws-analysis-card"}
                  onClick={() => setActiveId(obs.id)}
                >
                  <div className="ws-analysis-card-meta">
                    <span className="ws-crop-pill">{obs.crop_code}</span>
                    <Badge tone={obs.verification.status === "confirmed" ? "ok" : obs.verification.status === "probable" ? "warn" : "neutral"}>
                      {obs.verification.status}
                    </Badge>
                  </div>
                  <strong className="ws-analysis-title">Report #{obs.client_report_id.slice(0, 12)}</strong>
                  <p className="ws-analysis-sub">
                    Area: {obs.area_code} · {obs.variety ? `Variety: ${obs.variety}` : "Standard"}
                  </p>
                  <span className="ws-analysis-time">{formatDateTime(obs.submitted_at)}</span>
                </button>
              );
            })}
          </div>

          <div className="ws-analysis-detail">
            {active ? (
              <section className="ws-panel">
                <div className="ws-panel-head">
                  <div>
                    <p className="ws-eyebrow">Observation #{active.id.slice(0, 8)}</p>
                    <h2>{active.crop_code.toUpperCase()} — {active.area_code}</h2>
                  </div>
                  <Badge tone={active.verification.status === "confirmed" ? "ok" : "warn"}>
                    {active.verification.status}
                  </Badge>
                </div>

                <dl className="ws-detail-list">
                  <div>
                    <dt>Client report ID</dt>
                    <dd>{active.client_report_id}</dd>
                  </div>
                  <div>
                    <dt>Area code</dt>
                    <dd>{active.area_code}</dd>
                  </div>
                  <div>
                    <dt>Variety</dt>
                    <dd>{active.variety || "Not specified"}</dd>
                  </div>
                  <div>
                    <dt>Growth stage</dt>
                    <dd>{active.growth_stage || "Not recorded"}</dd>
                  </div>
                  <div>
                    <dt>Submitted at</dt>
                    <dd>{formatDateTime(active.submitted_at)}</dd>
                  </div>
                  <div>
                    <dt>Evidence tier</dt>
                    <dd>{active.verification.evidence_tier}</dd>
                  </div>
                </dl>

                {active.notes && (
                  <div className="ws-notice ws-notice-info">
                    <strong>Field notes:</strong> {active.notes}
                  </div>
                )}

                <div className="ws-panel-head" style={{ marginTop: "1.5rem" }}>
                  <div>
                    <p className="ws-eyebrow">Assistive AI assessment</p>
                    <h3>Model triage & confidence</h3>
                  </div>
                </div>

                {assessmentLoading ? (
                  <p className="ws-muted ws-small">Loading model assessment...</p>
                ) : activeAssessment ? (
                  <div>
                    <p className="ws-small">
                      <strong>State:</strong> {activeAssessment.state} · <strong>Model:</strong> {activeAssessment.model_version}
                    </p>
                    {activeAssessment.candidates && activeAssessment.candidates.length > 0 ? (
                      <div className="ws-stat-grid" style={{ marginTop: "0.5rem" }}>
                        {activeAssessment.candidates.map((cand) => (
                          <StatCard
                            key={cand.label}
                            label={cand.display_name || cand.label}
                            value={`${Math.round(cand.score * 100)}%`}
                            detail={`Confidence band: ${activeAssessment.confidence_band || "Uncalibrated"}`}
                            icon="leaf"
                            tone="brand"
                          />
                        ))}
                      </div>
                    ) : (
                      <p className="ws-muted ws-small">{activeAssessment.reason_text || "No candidates detected."}</p>
                    )}
                  </div>
                ) : (
                  <p className="ws-muted ws-small">No automated assessment attached to this observation record.</p>
                )}

                <div className="ws-banner-actions" style={{ marginTop: "1.5rem" }}>
                  {reviewedId === active.id ? (
                    <Badge tone="ok">Review requested with expert queue</Badge>
                  ) : (
                    <button
                      type="button"
                      className="ws-button ws-button-secondary"
                      onClick={() => void handleRequestReview()}
                    >
                      <Icon name="expert" size={16} /> Request expert verification
                    </button>
                  )}
                  <Link href={`/review`} className="ws-link">
                    Open expert queue
                  </Link>
                </div>
              </section>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

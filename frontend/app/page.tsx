import Link from "next/link";

import { ApiError, getHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Overview",
};

export default async function HomePage() {
  let service: string | null = null;
  let failure: string | null = null;

  try {
    const health = await getHealth();
    service = `${health.service} ${health.version} (${health.environment})`;
  } catch (error) {
    failure =
      error instanceof ApiError
        ? `${error.status} ${error.problem?.code ?? "api_error"}`
        : "API unreachable";
  }

  return (
    <div className="page ws-page">
      <header className="page-header">
        <p className="eyebrow">Overview</p>
        <h1>Crop early warning</h1>
        <p className="page-lede">
          An explainable, offline-tolerant decision-support workspace. It answers
          two separate questions and never merges them into one risk number.
        </p>
      </header>

      <section className="card" aria-labelledby="status-heading">
        <div className="panel-header">
          <h2 id="status-heading">Platform status</h2>
          {service ? (
            <span className="badge">API reachable</span>
          ) : (
            <span className="badge badge-muted">API unavailable</span>
          )}
        </div>
        {service ? (
          <p className="mono">{service}</p>
        ) : (
          <p className="error" role="status">
            {failure}
          </p>
        )}
        <p className="muted small">
          This panel reports platform reachability only. It does not report pest
          or disease risk.
        </p>
      </section>

      <section aria-labelledby="outputs-heading">
        <div className="section-heading">
          <h2 id="outputs-heading">Two outputs, never merged</h2>
          <p className="muted small">
            Different questions, different data, different timestamps.
          </p>
        </div>

        <div className="output-grid">
          <article className="output-card">
            <p className="eyebrow">Photo assessment</p>
            <h3>What might be visible on this plant?</h3>
            <p className="small muted">
              One image plus crop context. Assistive triage — not a diagnosis and
              not a laboratory result.
            </p>
            <p className="chip-row">
              <span className="chip">Assistive triage</span>
              <span className="chip chip-muted">Model & video pipelines</span>
            </p>
            <Link href="/chat" className="button">
              Open photo assessment
            </Link>
          </article>

          <article className="output-card output-card-muted">
            <p className="eyebrow">Area outlook</p>
            <h3>How likely is this threat in this area?</h3>
            <p className="small muted">
              Crop × target × geography × horizon. Weather and spatial risk
              indicators delivered with explicit coverage indicators.
            </p>
            <p className="chip-row">
              <span className="chip">Area forecasting</span>
              <span className="chip chip-muted">Coverage shown separately</span>
            </p>
            <Link href="/outlook" className="button button-secondary">
              View area outlook
            </Link>
          </article>
        </div>
      </section>

      <section aria-labelledby="sections-heading">
        <div className="section-heading">
          <h2 id="sections-heading">Workspace sections</h2>
          <p className="muted small">
            What is usable now, and what is still locked to a later phase.
          </p>
        </div>

        <div className="section-grid">
          <Link href="/chat" className="section-card">
            <span className="section-card-title">Photo assessment</span>
            <span className="small muted">
              Conversation list and thread, idempotent send and assistive triage.
            </span>
            <span className="badge">Available</span>
          </Link>

          <Link href="/review" className="section-card">
            <span className="section-card-title">Review queue</span>
            <span className="small muted">
              Expert verification portal. Scoped to extension workers and admins.
            </span>
            <span className="badge">Available</span>
          </Link>

          <Link href="/outlook" className="section-card">
            <span className="section-card-title">Area outlook</span>
            <span className="small muted">
              Forecast, risk map and coverage. Deliberately separate from photo
              assessment.
            </span>
            <span className="badge">Available</span>
          </Link>

          <Link href="/analysis" className="section-card">
            <span className="section-card-title">Observations & Analysis</span>
            <span className="small muted">
              Browse submitted observations, image assessments, and verification state.
            </span>
            <span className="badge">Available</span>
          </Link>

          <Link href="/admin" className="section-card">
            <span className="section-card-title">Administration</span>
            <span className="small muted">
              Provision staff, manage roles, inspect audits, and run retention.
            </span>
            <span className="badge">Admin only</span>
          </Link>
        </div>
      </section>

      <section className="card" aria-labelledby="safety-heading">
        <div className="panel-header">
          <h2 id="safety-heading">Safety & Decision Support Rules</h2>
          <span className="badge badge-muted">Safety R1–R10</span>
        </div>
        <p className="small muted">
          CropSentinel operates as assistive decision support only. Model outputs are never auto-promoted to verified cases (R4). Zero chemical recommendations are issued in demo content (R5). Missing and stale environmental inputs fail closed as insufficient data (R8).
        </p>
      </section>
    </div>
  );
}

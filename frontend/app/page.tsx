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
    <div className="page">
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
              <span className="chip">Demo replies only</span>
              <span className="chip chip-muted">No image model connected</span>
            </p>
            <Link href="/chat" className="button">
              Open photo assessment
            </Link>
          </article>

          <article className="output-card output-card-muted">
            <p className="eyebrow">Area outlook</p>
            <h3>How likely is this threat in this area?</h3>
            <p className="small muted">
              Crop × target × geography × horizon. Arrives in a later phase; no
              forecast is computed or shown in this build.
            </p>
            <p className="chip-row">
              <span className="chip chip-muted">Not available in this phase</span>
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
              Conversation list and thread, idempotent send and demo replies.
            </span>
            <span className="badge">Available</span>
          </Link>

          <Link href="/review" className="section-card">
            <span className="section-card-title">Review queue</span>
            <span className="small muted">
              Expert verification portal. Requires roles and review APIs that are
              not built yet.
            </span>
            <span className="badge badge-muted">Locked</span>
          </Link>

          <Link href="/outlook" className="section-card">
            <span className="section-card-title">Area outlook</span>
            <span className="small muted">
              Forecast, risk map and coverage. Deliberately separate from photo
              assessment.
            </span>
            <span className="badge badge-muted">Not in this phase</span>
          </Link>

          <Link href="/weather" className="section-card">
            <span className="section-card-title">Weather</span>
            <span className="small muted">
              Current conditions and a seven-day forecast for one location.
              Context only, never a risk score.
            </span>
            <span className="badge">Available</span>
          </Link>
        </div>
      </section>

      <section className="card" aria-labelledby="demo-heading">
        <div className="panel-header">
          <h2 id="demo-heading">Demo content</h2>
          <span className="badge badge-muted">demo</span>
        </div>
        <p className="small">
          The chat currently returns a labelled template reply. No image model is
          connected in this phase, and no assessment is fabricated.
        </p>
      </section>
    </div>
  );
}

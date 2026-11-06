import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Area outlook",
};

export default function OutlookPage() {
  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Area outlook</p>
        <h1>Area outlook</h1>
        <p className="page-lede">
          Crop × target × geography × horizon. This is a separate output from photo
          assessment, with its own data, model version and timestamp.
        </p>
      </header>

      <p className="notice notice-warning">
        <span className="badge badge-muted">not available</span> No area outlook is
        computed or shown in this phase. There is no forecast model, no verified
        coverage dataset and no agreed crop/target/geography list yet.
      </p>

      <section className="card" aria-labelledby="outlook-empty-heading">
        <h2 id="outlook-empty-heading">Not enough data for this area yet</h2>
        <p>
          An outlook requires verified reports, weather inputs and a coverage
          assessment for a defined area and window. None of those inputs exist in
          this build, so the platform does not issue a score.
        </p>
        <p className="small muted">
          No report is not evidence of absence. Absence of data is shown as “not
          enough data”, never as low risk.
        </p>
        <p>
          <Link href="/">Back to overview</Link>
        </p>
      </section>

      <section className="card" aria-labelledby="outlook-needs-heading">
        <h2 id="outlook-needs-heading">What must exist first</h2>
        <ul className="small">
          <li>Accepted crop, target and geography decisions (D1, D2).</li>
          <li>Verified case data and a coverage measure for each area.</li>
          <li>A rules baseline and, later, a validated forecast model.</li>
          <li>Calibration and a no-score gate approved before display.</li>
        </ul>
        <p className="small muted">
          Until then, photo assessment remains a separate assistive surface. Learn
          more in <code>final/docs-context/phase-plan.md</code> §7.
        </p>
      </section>
    </div>
  );
}

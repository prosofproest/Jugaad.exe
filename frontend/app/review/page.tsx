import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Review queue",
};

export default function ReviewPage() {
  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Expert portal</p>
        <h1>Review queue</h1>
        <p className="page-lede">
          The human verification surface for photo assessments. A model output is
          never auto-promoted to a verified case.
        </p>
      </header>

      <p className="notice notice-warning">
        <span className="badge badge-muted">locked</span> The review queue is not
        available in this phase. Authentication, five-role permissions and the
        review APIs are not built yet.
      </p>

      <section className="card" aria-labelledby="review-empty-heading">
        <h2 id="review-empty-heading">No cases can be shown yet</h2>
        <p>
          Nothing in this build creates a verification event. The replayed case
          list would be fabricated data, so it is deliberately not rendered.
        </p>
        <p className="small muted">
          Verification states: confirmed, probable, rejected, duplicate, needs
          visit, unresolved. Only a pathologist can set <strong>confirmed</strong>,
          and every change is audited.
        </p>
        <p>
          <Link href="/">Back to overview</Link>
        </p>
      </section>

      <section className="card" aria-labelledby="review-needs-heading">
        <h2 id="review-needs-heading">What must exist first</h2>
        <ul className="small">
          <li>Phone-OTP and provisioned staff accounts, with MFA for reviewers.</li>
          <li>Object-level access checks and audit events with a recorded reason.</li>
          <li>A review-request API shared with the structured and chat capture flows.</li>
          <li>An immutable decision history with evidence requirements per state.</li>
        </ul>
        <p className="small muted">
          This surface is specified in <code>final/feature-specs/04-expert-review.md</code>{" "}
          and scheduled in Phase 2 §5.6.
        </p>
      </section>
    </div>
  );
}
